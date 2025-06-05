import uuid

if __name__ == "__main__":
    import sys
    import os

    from core.Context import Context
    from coper.Mul import Mul

    with Context(task_id=str(uuid.uuid4())):

        print(f"3 * 2 = {Mul()(x=3, y=2).result()}")


