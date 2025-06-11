from core.Computable import Computable
from pydantic import BaseModel, Field


class UnaryInput(BaseModel):
    x: object = Field(..., description="single operand")


class BinaryInput(BaseModel):
    x: object = Field(..., description="first operand")
    y: object = Field(..., description="second operand")


class BasicOutput(BaseModel):
    result: object = Field(..., description="operation result")


# Arithmetic operations
class Add(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x + y"

    def compute(self, x, y):
        return x + y


class Subtract(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x - y"

    def compute(self, x, y):
        return x - y


class Multiply(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x * y"

    def compute(self, x, y):
        return x * y


class Mul(Multiply):
    pass


class Divide(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x / y"

    def compute(self, x, y):
        return x / y


class FloorDivide(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x // y"

    def compute(self, x, y):
        return x // y


class Modulo(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x % y"

    def compute(self, x, y):
        return x % y


class Power(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x ** y"

    def compute(self, x, y):
        return x ** y


# Bitwise operations
class BitwiseAnd(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x & y"

    def compute(self, x, y):
        return x & y


class BitwiseOr(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x | y"

    def compute(self, x, y):
        return x | y


class BitwiseXor(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x ^ y"

    def compute(self, x, y):
        return x ^ y


class LeftShift(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x << y"

    def compute(self, x, y):
        return x << y


class RightShift(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x >> y"

    def compute(self, x, y):
        return x >> y


# Comparison operations
class Equal(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x == y"

    def compute(self, x, y):
        return x == y


class NotEqual(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x != y"

    def compute(self, x, y):
        return x != y


class Less(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x < y"

    def compute(self, x, y):
        return x < y


class LessEqual(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x <= y"

    def compute(self, x, y):
        return x <= y


class Greater(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x > y"

    def compute(self, x, y):
        return x > y


class GreaterEqual(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x >= y"

    def compute(self, x, y):
        return x >= y


# Logical operations
class LogicalAnd(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x and y"

    def compute(self, x, y):
        return x and y


class LogicalOr(Computable):
    input_schema = BinaryInput
    output_schema = BasicOutput
    description = "Return x or y"

    def compute(self, x, y):
        return x or y


class LogicalNot(Computable):
    input_schema = UnaryInput
    output_schema = BasicOutput
    description = "Return not x"

    def compute(self, x):
        return not x


# Unary operations
class Negate(Computable):
    input_schema = UnaryInput
    output_schema = BasicOutput
    description = "Return -x"

    def compute(self, x):
        return -x


class Invert(Computable):
    input_schema = UnaryInput
    output_schema = BasicOutput
    description = "Return bitwise inversion of x"

    def compute(self, x):
        return ~x
