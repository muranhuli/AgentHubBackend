import numpy as np
import random
from core.Context import Context
import uuid
from coper.Embedding import Embedding
import time

if __name__ == "__main__":
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        start = time.time()
        embedding = Embedding()
        text = ["Hello, world!", 'dsjkdjks']
        result = embedding(text).result()
        print(f"Embedding result: {result}")
        text = "Hello, world!"
        result = embedding(text).result()
        print(f"Embedding result: {result}")
        end = time.time()
        print(f"Time taken: {end - start} seconds")