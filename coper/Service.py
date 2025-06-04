import json
import uuid

from core.Computable import Computable


class Service(Computable):

    def __init__(self, service_id):
        super().__init__()
        self.service_id = service_id


    def compute(self, *args):
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
            properties=self.ch.Properties(
                delivery_mode=2
            )
        )

        _, res = self.redis.blpop([return_queue])
        self.redis.delete(return_queue)
        response = json.loads(res)
        if response['status'] == 'error':
            raise Exception(response['message'])
        return response['result']



