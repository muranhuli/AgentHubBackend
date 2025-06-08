import json

import pika

from core.ComputableResult import ComputableResult
from core.Context import get_context


class Computable:
    """算子基类。

    Subclasses should implement :meth:`compute` and provide ``input_schema``,
    ``output_schema`` and ``description`` to describe the operator. These can be
    defined as class attributes.
    """

    #: Pydantic model describing the expected inputs of this computable.
    input_schema = None

    #: Pydantic model describing the outputs of this computable.
    output_schema = None

    #: Human readable description of the computable's capability.
    description = ""

    def __init__(self, *args, **kwargs):
        self.ctx = get_context()
        self.redis = self.ctx.redis
        self.ch = self.ctx.channel
        self.minio = self.ctx.minio
        self.init_args = args
        self.init_kwargs = kwargs
        # Copy class level descriptions so each instance carries them
        self.description = getattr(self.__class__, 'description', '')
        self.input_schema = getattr(self.__class__, 'input_schema', None)
        self.output_schema = getattr(self.__class__, 'output_schema', None)

    def __call__(self, *args, **kwargs):
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

        kwarg_dict = {}
        for k, v in kwargs.items():
            if isinstance(v, ComputableResult):
                kwarg_dict[k] = {"is_ref": True, "exec_id": v.exec_id}
                dep_list.append(v.exec_id)
            else:
                kwarg_dict[k] = {"is_ref": False, "value": v}

        job = {
            "exec_id": exec_id,
            "task_id": task_id,
            "task": self.__class__.__name__,
            "args": arg_list,
            "kwargs": kwarg_dict,
            "init_args": self.init_args,
            "init_kwargs": self.init_kwargs,
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

    def compute(self, *args, **kwargs):
        raise NotImplementedError("compute must return a value or raise")
