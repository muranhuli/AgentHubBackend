import json
import importlib
import multiprocessing

import pika

from core.ComputableResult import ComputableResult
from core.Context import get_context, Context
from core.Utils import deserialize, serialize


class Runner:
    def __init__(self):
        self.ctx = get_context()
        self.redis = self.ctx.redis
        self.ch = self.ctx.channel

    def start(self):
        self.ch.basic_consume(queue=self.ctx.queue, on_message_callback=self._on_message)
        self.ch.start_consuming()

    def _on_message(self, ch, method, props, body):
        """
        job = {
            "exec_id": "12345",
            "task_id": "task_1",
            "task": "example_task",
            "args": [
                {"is_ref": True, "exec_id": "12344"},
                {"is_ref": False, "value": 42}
            ]
        }
        redis data structure:
        1. hash: runner-node:{task_id}
                 job:{exec_id} string (任务定义)
                 state:{exec_id} string (状态, 可选值: PENDING, RUNNING, FINISHED, ERROR)
                 dep:{exec_id} string (依赖的任务 ID, 逗号隔开)
                 dep_cnt:{exec_id} int (任务依赖计数)
                 finish_pointer:{exec_id} string (任务完成指针, 当前任务完成时，outer才算完成)
        2. set: runner-node-waiters:{task_id}:{exec_id} (子任务等待队列)
        3. int: runner-node-counter:{task_id} (任务计数，用于分配 exec_id)
        4. list: runner-node-result:{task_id}:{exec_id} string (结果 / 错误信息)

        """
        job = deserialize(body)
        exec_id = job["exec_id"]
        task_id = job["task_id"]

        # 设置当前上下文的任务 ID
        self.ctx.set_task(task_id)

        task_key = f"runner-node:{task_id}"
        result_key = f"runner-node-result:{task_id}:{exec_id}"

        try:
            self.redis.hset(task_key, f"state:{exec_id}", "RUNNING")
            args = []

            def get_value(exec_id_):
                key = f"runner-node-result:{task_id}:{exec_id_}"
                state = self.redis.hget(task_key, f"state:{exec_id_}")
                if state == "ERROR":
                    raise RuntimeError(f"Previous task {arg['exec_id']} failed")
                raw = self.redis.lrange(key, 0, -1)[0]
                return deserialize(raw)

            def get_value_obj(obj):
                if isinstance(obj, ComputableResult):
                    return get_value(obj.exec_id)
                elif isinstance(obj, dict):
                    return {get_value_obj(k): get_value_obj(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [get_value_obj(item) for item in obj]
                elif isinstance(obj, tuple):
                    return tuple(get_value_obj(item) for item in obj)
                else:
                    return obj

            for arg in job["args"]:
                args.append(get_value_obj(arg))
            kwargs = {}
            for k, v in job.get("kwargs", {}).items():
                kwargs[k] = get_value_obj(v)

            # 动态加载 operator 并执行
            module_path, cls_name = job["task"].rsplit(".", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, cls_name)
            init_args = job.get("init_args", [])
            init_kwargs = job.get("init_kwargs", {})
            instance = cls(*init_args, **init_kwargs)
            compute = instance.compute

            res = compute(*args, **kwargs)
        except Exception as e:
            # 获取递归栈
            import traceback
            stack = traceback.format_exc()
            self.redis.hset(task_key, f"state:{exec_id}", "ERROR")
            self.redis.lpush(result_key, serialize({"error": str(e), "stack": stack})[1])
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"任务 {exec_id} 执行失败: {e}")
            print(stack)
            # raise RuntimeError(f"任务 {exec_id} 执行失败: {e}")
        else:
            # 成功
            if isinstance(res, ComputableResult):
                # 如果是 ComputableResult 类型，说明当前的任务还没有完成
                last_exec_id = res.exec_id
                # 更新 finish_pointer
                self.redis.hset(task_key, f"finish_pointer:{last_exec_id}", str(exec_id))
            else:
                finish_exec_id_list = [exec_id]
                while True:
                    now_exec_id = finish_exec_id_list[-1]
                    last_exec_id = self.redis.hget(task_key, f"finish_pointer:{now_exec_id}")
                    if last_exec_id is None:
                        break
                    finish_exec_id_list.append(int(last_exec_id))

                for feid in finish_exec_id_list:
                    self.redis.hset(task_key, f"state:{feid}", "FINISHED")
                    self.redis.lpush(f"runner-node-result:{task_id}:{feid}", serialize(res)[1])
                    # 调度子任务
                    children = self.redis.smembers(f"runner-node-waiters:{task_id}:{feid}") or []
                    for cid in children:
                        cnt = self.redis.hincrby(task_key, f"dep_cnt:{cid}", -1)
                        if cnt == 0:
                            # 发布到同一个队列
                            self.ch.basic_publish(
                                exchange='',
                                routing_key=self.ctx.queue,
                                body=self.redis.hget(task_key, f"job:{cid}").encode('latin1'),
                                properties=pika.BasicProperties(delivery_mode=2)
                            )
            ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == "__main__":
    def run():
        with Context():
            runner = Runner()
            runner.start()


    mpl = []
    for _ in range(16):
        p = multiprocessing.Process(target=run)
        p.start()
        mpl.append(p)

    for p in mpl:
        p.join()
