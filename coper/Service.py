import json
import uuid

import pika

from core.Computable import Computable
from core.Utils import serialize


class Service(Computable):
    """Invoke a remote service."""

    def __init__(self, service_id):
        super().__init__(service_id)
        self.service_id = service_id


    def compute(self, *args, **kwargs) -> object:
        """Invoke the remote service with the provided arguments."""

        return_id = str(uuid.uuid4().hex)
        return_queue = f"service-response:{self.service_id}:{return_id}"
        request = {
            'task_id': self.ctx.task,
            'return_queue': return_queue,
            'args': args,
            'kwargs': kwargs,
        }

        self.ch.basic_publish(
            exchange='',
            routing_key=f"service.request.{self.service_id}",
            body=serialize(request)[0],
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        _, res = self.redis.blpop([return_queue])
        self.redis.delete(return_queue)
        response = json.loads(res)
        if response['status'] == 'error':
            print(response["stack"])
            raise Exception(response['message'])
        return response['result']



