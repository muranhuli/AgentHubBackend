import json
import uuid

import pika
from pydantic import BaseModel, Field

from core.Computable import Computable


class ServiceInput(BaseModel):
    """Input model for :class:`Service`."""

    args: list = Field(default_factory=list, description="Positional arguments")


class ServiceOutput(BaseModel):
    """Output model for :class:`Service`."""

    result: object = Field(..., description="Result returned from service")


class Service(Computable):
    """Invoke a remote service."""

    input_schema = ServiceInput
    output_schema = ServiceOutput
    description = "Call a registered service"

    def __init__(self, service_id):
        super().__init__(service_id)
        self.service_id = service_id


    def compute(self, *args) -> object:
        """Invoke the remote service with the provided arguments."""

        return_id = str(uuid.uuid4().hex)
        return_queue = f"service-response:{self.service_id}:{return_id}"
        request = {
            'return_queue': return_queue,
            'args': args
        }
        self.ch.basic_publish(
            exchange='',
            routing_key=f"service.request.{self.service_id}",
            body=json.dumps(request),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        _, res = self.redis.blpop([return_queue])
        self.redis.delete(return_queue)
        response = json.loads(res)
        if response['status'] == 'error':
            raise Exception(response['message'])
        return response['result']



