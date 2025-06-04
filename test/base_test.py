import time
import uuid

from coper.Add import Add
from coper.Mul import Mul
from coper.Test import Test
from core.Context import Context



if __name__ == '__main__':
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        add = Test()
        mul = Mul()

        t = time.time()
        for _ in range(10):
            # 链式调用，自动管理依赖
            r1 = add(1, 2)       # <Result id=1 state=RUNNING>
            r2 = add(3, 4)       # <Result id=1 state=RUNNING>
            r3 = mul(r1, r2)     # <Result id=2 state=PENDING>
            r4 = r1 + r2 * r3 # 150


            # 同步获取结果，无需 await
            # print('r1 =', r1.result())  # 3
            # print('r2 =', r2.result())  # 7
            # print('r3 =', r3.result())  # 21
        print('r4 =', r4.result()) # 21 * 11 = 231

        print(time.time() - t)
