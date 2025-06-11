import json
from core.Context import get_context
from core.Utils import deserialize


# 逻辑非运算（不能重载 not，提供方法代替）
def logical_not(self):
    from coper.basic_ops import LogicalNot
    return LogicalNot()(self)

# 显式逻辑与/或（不能重载 and/or）
def logical_and(self, other):
    from coper.basic_ops import LogicalAnd
    return LogicalAnd()(self, other)

def logical_or(self, other):
    from coper.basic_ops import LogicalOr
    return LogicalOr()(self, other)


class ComputableResult:
    """
    任务结果句柄，提供同步 .result() 方法阻塞获取或抛出异常。
    """

    def __init__(self, exec_id: int):
        self.exec_id = exec_id
        self.ctx = get_context()

    def result(self):
        task_id = self.ctx.task
        r = self.ctx.redis
        res_list_name = f"runner-node-result:{task_id}:{self.exec_id}"
        _, res = r.blpop([res_list_name])
        r.rpush(res_list_name, res)

        res = deserialize(res)
        state = r.hget(f"runner-node:{task_id}", f"state:{self.exec_id}")
        if state == "FINISHED":
            return res

        raise Exception(res)

    def __getstate__(self):
        return {"exec_id": self.exec_id}

    def __setstate__(self, state):
        self.exec_id = state["exec_id"]
        self.ctx = get_context()

    def __repr__(self):
        return f"<Result id={self.exec_id}>"

    # 二元运算符
    def __add__(self, other):
        from coper.basic_ops import Add
        return Add()(self, other)

    def __radd__(self, other):
        from coper.basic_ops import Add
        return Add()(other, self)

    def __sub__(self, other):
        from coper.basic_ops import Subtract
        return Subtract()(self, other)

    def __rsub__(self, other):
        from coper.basic_ops import Subtract
        return Subtract()(other, self)

    def __mul__(self, other):
        from coper.basic_ops import Multiply
        return Multiply()(self, other)

    def __rmul__(self, other):
        from coper.basic_ops import Multiply
        return Multiply()(other, self)

    def __truediv__(self, other):
        from coper.basic_ops import Divide
        return Divide()(self, other)

    def __rtruediv__(self, other):
        from coper.basic_ops import Divide
        return Divide()(other, self)

    def __floordiv__(self, other):
        from coper.basic_ops import FloorDivide
        return FloorDivide()(self, other)

    def __rfloordiv__(self, other):
        from coper.basic_ops import FloorDivide
        return FloorDivide()(other, self)

    def __mod__(self, other):
        from coper.basic_ops import Modulo
        return Modulo()(self, other)

    def __rmod__(self, other):
        from coper.basic_ops import Modulo
        return Modulo()(other, self)

    def __pow__(self, other):
        from coper.basic_ops import Power
        return Power()(self, other)

    def __rpow__(self, other):
        from coper.basic_ops import Power
        return Power()(other, self)

    def __and__(self, other):
        from coper.basic_ops import BitwiseAnd
        return BitwiseAnd()(self, other)

    def __rand__(self, other):
        from coper.basic_ops import BitwiseAnd
        return BitwiseAnd()(other, self)

    def __or__(self, other):
        from coper.basic_ops import BitwiseOr
        return BitwiseOr()(self, other)

    def __ror__(self, other):
        from coper.basic_ops import BitwiseOr
        return BitwiseOr()(other, self)

    def __xor__(self, other):
        from coper.basic_ops import BitwiseXor
        return BitwiseXor()(self, other)

    def __rxor__(self, other):
        from coper.basic_ops import BitwiseXor
        return BitwiseXor()(other, self)

    def __lshift__(self, other):
        from coper.basic_ops import LeftShift
        return LeftShift()(self, other)

    def __rlshift__(self, other):
        from coper.basic_ops import LeftShift
        return LeftShift()(other, self)

    def __rshift__(self, other):
        from coper.basic_ops import RightShift
        return RightShift()(self, other)

    def __rrshift__(self, other):
        from coper.basic_ops import RightShift
        return RightShift()(other, self)

    def __eq__(self, other):
        from coper.basic_ops import Equal
        return Equal()(self, other)

    def __ne__(self, other):
        from coper.basic_ops import NotEqual
        return NotEqual()(self, other)

    def __lt__(self, other):
        from coper.basic_ops import Less
        return Less()(self, other)

    def __le__(self, other):
        from coper.basic_ops import LessEqual
        return LessEqual()(self, other)

    def __gt__(self, other):
        from coper.basic_ops import Greater
        return Greater()(self, other)

    def __ge__(self, other):
        from coper.basic_ops import GreaterEqual
        return GreaterEqual()(self, other)

    # 一元运算符
    def __neg__(self):
        from coper.basic_ops import Negate
        return Negate()(self)

    def __invert__(self):
        from coper.basic_ops import Invert
        return Invert()(self)

    def __bool__(self):
        raise TypeError("Cannot use ComputableResult in boolean context")


# 将逻辑方法绑定到 ComputableResult
ComputableResult.logical_not = logical_not
ComputableResult.logical_and = logical_and
ComputableResult.logical_or = logical_or
