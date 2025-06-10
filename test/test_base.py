import uuid

if __name__ == "__main__":
    import sys
    import os

    from core.Context import Context
    from coper.Mul import Mul
    from coper.Add import Add

    with Context(task_id=str(uuid.uuid4())):
        mul = Mul()
        add = Add()

        a = mul(3, 2)
        b = add(3, 2)

        c = add(a, b)


        print(f"{c.result()}")


