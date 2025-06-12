import uuid

if __name__ == "__main__":
    from core.Context import Context
    from coper.basic_ops import Mul
    from coper.basic_ops import Add

    with Context(task_id=str(uuid.uuid4())):
        mul = Mul()
        add = Add()

        a = mul(3, 2)
        b = add(3, 2)

        c = add(a, b)


        print(f"{c.result()}")


