import json

import pika

from core.ComputableResult import ComputableResult
from core.Context import get_context


class Computable:
    """
    算子基类：实现 compute(self, *args) 即可。
    调用时自动使用当前 Runner，上下文管理无需 await。
    """

    def __init__(self):
        self.ctx = get_context()
        self.redis = self.ctx.redis
        self.ch = self.ctx.channel

    def __call__(self, *args):
        task_id = self.ctx.task
        task_key = f"runner-node:{task_id}"
        task_waiter_key = f"runner-node-waiters:{task_id}"

        # 原子自增 exec_id
        exec_id = self.redis.incr(f"runner-node-counter:{task_id}")

        arg_list = []
        dep_list = []
        for arg in args:
            if isinstance(arg, ComputableResult):
                arg_list.append({"is_ref": True, "exec_id": arg.exec_id})
                dep_list.append(arg.exec_id)
            else:
                arg_list.append({"is_ref": False, "value": arg})

        job = {
            "exec_id": exec_id,
            "task_id": task_id,
            "task": self.__class__.__name__,
            "args": arg_list,
            "service_id": self.service_id if hasattr(self, 'service_id') else None,
        }

        dep = ",".join(str(dep) for dep in dep_list)

        # 原子写入状态、依赖、job
        dep_cnt = self.ctx.init_task(keys=[task_key, task_waiter_key], args=[exec_id, json.dumps(job), dep])

        # 依赖为 0 时，直接发布到 RabbitMQ
        if dep_cnt == 0:
            self.ch.basic_publish(
                exchange='',
                routing_key=self.ctx.queue,
                body=json.dumps(job),
                properties=pika.BasicProperties(delivery_mode=2)
            )

        return ComputableResult(exec_id)

    def compute(self, *args):
        raise NotImplementedError("compute must return a value or raise")
