import time
import uuid

from coper.Add import Add
from coper.Mul import Mul
from coper.Test import Test
from core.Context import Context
from coper.Service import Service



if __name__ == '__main__':
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        add = Test()
        mul = Mul()
        search = Service("local-web-search")
        res = search("What is the capital of France?", "google", 3)
        res = res.result()
        print(res)

