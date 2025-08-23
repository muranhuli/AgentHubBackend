# redislock.py

import redis
import uuid
import threading
import time
from typing import Optional, Callable

class Lease:
    """代表一次持有的租约"""
    def __init__(self, problem_key: str, token: str, fence: int):
        self.problem_key = problem_key
        self.token = token
        self.fence = fence
        self._alive = True
        self._lost_reason = None
        self._on_lost = None  # type: Optional[Callable[[str], None]]

    @property
    def alive(self) -> bool:
        return self._alive

    @property
    def lost_reason(self) -> Optional[str]:
        return self._lost_reason

    def set_on_lost(self, cb: Callable[[str], None]):
        self._on_lost = cb

    def _mark_lost(self, reason: str):
        if self._alive:
            self._alive = False
            self._lost_reason = reason
            if self._on_lost:
                try:
                    self._on_lost(reason)
                except Exception:
                    # 回调内部异常不传播，避免影响主流程
                    pass

class RedisLock:
    """
    基于 Redis 的分布式锁（SET NX + TTL），支持：
    - fencing token（INCR）
    - 心跳续租（后台线程，Lua 校验 token）
    - 上下文管理（自动释放/停止心跳）
    """
    _RELEASE_LUA = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
      return redis.call('del', KEYS[1])
    else
      return 0
    end
    """
    _REFRESH_LUA = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
      return redis.call('pexpire', KEYS[1], ARGV[2])
    else
      return 0
    end
    """

    def __init__(self, redis_client: redis.Redis, lock_ttl_ms: int = 60_000,
                 refresh_interval_ms: Optional[int] = None, jitter_ms: int = 200):
        """
        :param redis_client: 已连接的 redis.Redis 实例
        :param lock_ttl_ms: 锁租约 TTL（毫秒）
        :param refresh_interval_ms: 心跳周期（毫秒），默认取 ttl * 0.4
        :param jitter_ms: 心跳抖动（毫秒），避免雪崩
        """
        if not isinstance(redis_client, redis.Redis):
            raise TypeError("redis_client must be an instance of redis.Redis")

        self.r = redis_client
        self.lock_ttl_ms = int(lock_ttl_ms)
        # 确保心跳间隔至少为1秒，且小于TTL
        self.refresh_interval_ms = int(refresh_interval_ms or max(1000, lock_ttl_ms * 4 // 10))
        self.jitter_ms = int(jitter_ms)

        if self.refresh_interval_ms >= self.lock_ttl_ms:
            raise ValueError("refresh_interval_ms must be less than lock_ttl_ms")


    def _lock_key(self, problem_key: str) -> str:
        return f"lock:{problem_key}"

    def _fence_key(self, problem_key: str) -> str:
        return f"lock:fence:{problem_key}"

    def acquire(self, problem_key: str) -> Optional[Lease]:
        """尝试获取锁，返回 Lease 对象或 None"""
        token = str(uuid.uuid4())
        # 原子性地获取并递增 fence 值
        fence = self.r.incr(self._fence_key(problem_key))
        # 尝试设置锁，只有当键不存在时才成功 (NX)，并设置过期时间 (PX)
        ok = self.r.set(self._lock_key(problem_key), token, nx=True, px=self.lock_ttl_ms)
        if ok:
            return Lease(problem_key, token, fence)
        return None

    def release(self, lease: Lease) -> bool:
        """安全地释放锁，使用 Lua 脚本校验 token"""
        if not isinstance(lease, Lease):
            return False
        try:
            # Lua 脚本保证了 get 和 del 的原子性
            res = self.r.eval(self._RELEASE_LUA, 1, self._lock_key(lease.problem_key), lease.token)
            return bool(res)
        except redis.RedisError as e:
            print(f"Error releasing lock for {lease.problem_key}: {e}")
            return False

    def refresh_once(self, lease: Lease) -> bool:
        """单次续租，使用 Lua 脚本校验 token 并更新 TTL"""
        if not isinstance(lease, Lease):
            return False
        try:
            # Lua 脚本保证了 get 和 pexpire 的原子性
            res = self.r.eval(self._REFRESH_LUA, 1, self._lock_key(lease.problem_key),
                              lease.token, self.lock_ttl_ms)
            return bool(res)
        except redis.RedisError as e:
            print(f"Error refreshing lock for {lease.problem_key}: {e}")
            return False

    def hold(self, problem_key: str, on_lost: Optional[Callable[[str], None]] = None):
        """
        上下文管理器：使用 'with lock.hold(problem_key) as lease:' 语法
        进入时获取锁并启动心跳，退出时停止心跳并释放锁。
        若获取失败，返回 None。
        """
        lease = self.acquire(problem_key)
        if lease:
            lease.set_on_lost(on_lost) # 注册租约丢失时的回调
        return _LeaseContext(self, lease, self.refresh_interval_ms, self.jitter_ms)

class _LeaseContext:
    """Lease 的上下文管理器，负责启动/停止心跳线程"""
    def __init__(self, lock: RedisLock, lease: Optional[Lease], refresh_interval_ms: int, jitter_ms: int):
        self.lock = lock
        self.lease = lease
        self.refresh_interval_ms = refresh_interval_ms
        self.jitter_ms = jitter_ms
        self._stop = threading.Event() # 用于通知心跳线程停止
        self._thread = None

    def __enter__(self) -> Optional[Lease]:
        """进入 with 块，如果成功获取锁，则启动心跳线程"""
        if not self.lease:
            return None # 未获取到锁

        # 启动心跳线程
        self._thread = threading.Thread(
            target=self._refresh_loop,
            name=f"lease-heartbeat-{self.lease.problem_key}",
            daemon=True # 设置为守护线程，主程序退出时会自动结束
        )
        self._thread.start()
        return self.lease

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出 with 块，停止心跳并释放锁"""
        # 停止心跳线程
        if self._thread:
            self._stop.set() # 发送停止信号
            self._thread.join(timeout=2.0) # 等待线程结束，最多2秒

        # 如果当前仍然持有有效的 lease，则尝试释放锁
        if self.lease and self.lease.alive:
            try:
                self.lock.release(self.lease)
                print(f"Released lock for {self.lease.problem_key}")
            except Exception as e:
                print(f"Error during lock release for {self.lease.problem_key}: {e}")

        # 返回 False 表示不吞噬在 with 块中发生的异常
        return False

    def _refresh_loop(self):
        """心跳续租循环"""
        lease = self.lease
        # 预计算下一次休眠时间，加上抖动
        next_sleep_duration = (self.refresh_interval_ms + self._calculate_jitter()) / 1000.0

        while not self._stop.is_set() and lease and lease.alive:
            try:
                # 等待，直到收到停止信号或超时
                slept = self._stop.wait(timeout=next_sleep_duration)
                if slept:  # 如果收到了停止信号，直接退出循环
                    break

                # 尝试续租
                ok = self.lock.refresh_once(lease)
                if not ok:
                    # 续租失败，标记租约丢失
                    lease._mark_lost("lease_lost_or_token_mismatch")
                    print(f"Heartbeat failed for {lease.problem_key}. Lease lost.")
                    break # 退出循环

                # 续租成功，计算下一次休眠时间
                next_sleep_duration = (self.refresh_interval_ms + self._calculate_jitter()) / 1000.0

            except Exception as e:
                print(f"Error in heartbeat loop for {lease.problem_key}: {e}")
                # 发生未知异常时，也标记为丢失，并退出
                lease._mark_lost(f"heartbeat_error: {e}")
                break

    def _calculate_jitter(self) -> int:
        """计算一个随机的抖动值"""
        # 简单的抖动：返回一个在 [-jitter_ms/2, +jitter_ms/2] 范围内的整数
        # time.time() % 1 产生一个 [0, 1) 的值
        # 0.5 - time.time() % 1 产生一个 [-0.5, 0.5) 的值
        # 乘以 jitter_ms 得到一个大致在 [-jitter_ms/2, +jitter_ms/2] 的浮点数
        # int() 截断小数部分
        return int((0.5 - time.time() % 1) * self.jitter_ms)