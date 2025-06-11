from core.Computable import Computable
from pydantic import BaseModel, Field


# Arithmetic operations
class AddInput(BaseModel):
    """Input model for :class:`Add`."""

    x: float = Field(..., description="First operand")
    y: float = Field(..., description="Second operand")

class AddOutput(BaseModel):
    """Output model for :class:`Add`."""

    result: float = Field(..., description="Sum of ``x`` and ``y``")

class Add(Computable):
    """Add two numbers."""

    input_schema = AddInput
    output_schema = AddOutput
    description = "Return the sum of two numbers"

    def compute(self, x: float, y: float) -> float:
        """Return the sum of ``x`` and ``y``."""

        return x + y


class SubtractInput(BaseModel):
    """Input model for :class:`Subtract`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class SubtractOutput(BaseModel):
    """Output model for :class:`Subtract`."""

    result: float = Field(..., description="Result of ``x - y``")

class Subtract(Computable):
    """Subtraction operation."""

    input_schema = SubtractInput
    output_schema = SubtractOutput
    description = "Return x - y"

    def compute(self, x: float, y: float) -> float:
        """Return ``x`` minus ``y``."""

        return x - y


class MultiplyInput(BaseModel):
    """Input model for :class:`Multiply`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class MultiplyOutput(BaseModel):
    """Output model for :class:`Multiply`."""

    result: float = Field(..., description="Result of ``x * y``")

class Multiply(Computable):
    """Multiply two numbers."""

    input_schema = MultiplyInput
    output_schema = MultiplyOutput
    description = "Return x * y"

    def compute(self, x: float, y: float) -> float:
        """Return the product of ``x`` and ``y``."""

        return x * y


class MulInput(BaseModel):
    """Input model for :class:`Mul`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class MulOutput(BaseModel):
    """Output model for :class:`Mul`."""

    result: float = Field(..., description="Result of ``x * y``")

class Mul(Computable):
    """Multiplication operation."""

    input_schema = MulInput
    output_schema = MulOutput
    description = "Return x * y"

    def compute(self, x: float, y: float) -> float:
        """Return the product of ``x`` and ``y``."""

        return x * y


class DivideInput(BaseModel):
    """Input model for :class:`Divide`."""

    x: float = Field(..., description="Dividend")
    y: float = Field(..., description="Divisor")

class DivideOutput(BaseModel):
    """Output model for :class:`Divide`."""

    result: float = Field(..., description="Quotient of ``x / y``")

class Divide(Computable):
    """Division operation."""

    input_schema = DivideInput
    output_schema = DivideOutput
    description = "Return x divided by y"

    def compute(self, x: float, y: float) -> float:
        """Return ``x`` divided by ``y``."""

        return x / y


class FloorDivideInput(BaseModel):
    """Input model for :class:`FloorDivide`."""

    x: float = Field(..., description="Dividend")
    y: float = Field(..., description="Divisor")

class FloorDivideOutput(BaseModel):
    """Output model for :class:`FloorDivide`."""

    result: float = Field(..., description="Result of ``x // y``")

class FloorDivide(Computable):
    """Floor division."""

    input_schema = FloorDivideInput
    output_schema = FloorDivideOutput
    description = "Return x // y"

    def compute(self, x: float, y: float) -> float:
        """Return ``x`` floor-divided by ``y``."""

        return x // y


class ModuloInput(BaseModel):
    """Input model for :class:`Modulo`."""

    x: float = Field(..., description="Dividend")
    y: float = Field(..., description="Divisor")

class ModuloOutput(BaseModel):
    """Output model for :class:`Modulo`."""

    result: float = Field(..., description="Result of ``x % y``")

class Modulo(Computable):
    """Modulo operation."""

    input_schema = ModuloInput
    output_schema = ModuloOutput
    description = "Return x % y"

    def compute(self, x: float, y: float) -> float:
        """Return the remainder of ``x`` divided by ``y``."""

        return x % y


class PowerInput(BaseModel):
    """Input model for :class:`Power`."""

    x: float = Field(..., description="Base value")
    y: float = Field(..., description="Exponent")

class PowerOutput(BaseModel):
    """Output model for :class:`Power`."""

    result: float = Field(..., description="Result of ``x ** y``")

class Power(Computable):
    """Exponentiation operation."""

    input_schema = PowerInput
    output_schema = PowerOutput
    description = "Return x ** y"

    def compute(self, x: float, y: float) -> float:
        """Return ``x`` raised to the ``y`` power."""

        return x ** y


# Bitwise operations
class BitwiseAndInput(BaseModel):
    """Input model for :class:`BitwiseAnd`."""

    x: int = Field(..., description="Left operand")
    y: int = Field(..., description="Right operand")

class BitwiseAndOutput(BaseModel):
    """Output model for :class:`BitwiseAnd`."""

    result: int = Field(..., description="Result of ``x & y``")

class BitwiseAnd(Computable):
    """Bitwise AND operation."""

    input_schema = BitwiseAndInput
    output_schema = BitwiseAndOutput
    description = "Return x & y"

    def compute(self, x: int, y: int) -> int:
        """Return the bitwise AND of ``x`` and ``y``."""

        return x & y


class BitwiseOrInput(BaseModel):
    """Input model for :class:`BitwiseOr`."""

    x: int = Field(..., description="Left operand")
    y: int = Field(..., description="Right operand")

class BitwiseOrOutput(BaseModel):
    """Output model for :class:`BitwiseOr`."""

    result: int = Field(..., description="Result of ``x | y``")

class BitwiseOr(Computable):
    """Bitwise OR operation."""

    input_schema = BitwiseOrInput
    output_schema = BitwiseOrOutput
    description = "Return x | y"

    def compute(self, x: int, y: int) -> int:
        """Return the bitwise OR of ``x`` and ``y``."""

        return x | y


class BitwiseXorInput(BaseModel):
    """Input model for :class:`BitwiseXor`."""

    x: int = Field(..., description="Left operand")
    y: int = Field(..., description="Right operand")

class BitwiseXorOutput(BaseModel):
    """Output model for :class:`BitwiseXor`."""

    result: int = Field(..., description="Result of ``x ^ y``")

class BitwiseXor(Computable):
    """Bitwise XOR operation."""

    input_schema = BitwiseXorInput
    output_schema = BitwiseXorOutput
    description = "Return x ^ y"

    def compute(self, x: int, y: int) -> int:
        """Return the bitwise XOR of ``x`` and ``y``."""

        return x ^ y


class LeftShiftInput(BaseModel):
    """Input model for :class:`LeftShift`."""

    x: int = Field(..., description="Value to shift")
    y: int = Field(..., description="Number of bits")

class LeftShiftOutput(BaseModel):
    """Output model for :class:`LeftShift`."""

    result: int = Field(..., description="Result of ``x << y``")

class LeftShift(Computable):
    """Bitwise left shift."""

    input_schema = LeftShiftInput
    output_schema = LeftShiftOutput
    description = "Return x << y"

    def compute(self, x: int, y: int) -> int:
        """Return ``x`` left-shifted by ``y`` bits."""

        return x << y


class RightShiftInput(BaseModel):
    """Input model for :class:`RightShift`."""

    x: int = Field(..., description="Value to shift")
    y: int = Field(..., description="Number of bits")

class RightShiftOutput(BaseModel):
    """Output model for :class:`RightShift`."""

    result: int = Field(..., description="Result of ``x >> y``")

class RightShift(Computable):
    """Bitwise right shift."""

    input_schema = RightShiftInput
    output_schema = RightShiftOutput
    description = "Return x >> y"

    def compute(self, x: int, y: int) -> int:
        """Return ``x`` right-shifted by ``y`` bits."""

        return x >> y


# Comparison operations
class EqualInput(BaseModel):
    """Input model for :class:`Equal`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class EqualOutput(BaseModel):
    """Output model for :class:`Equal`."""

    result: bool = Field(..., description="Result of ``x == y``")

class Equal(Computable):
    """Check equality."""

    input_schema = EqualInput
    output_schema = EqualOutput
    description = "Return True if x == y"

    def compute(self, x: float, y: float) -> bool:
        """Return ``True`` if ``x`` equals ``y``."""

        return x == y


class NotEqualInput(BaseModel):
    """Input model for :class:`NotEqual`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class NotEqualOutput(BaseModel):
    """Output model for :class:`NotEqual`."""

    result: bool = Field(..., description="Result of ``x != y``")

class NotEqual(Computable):
    """Inequality comparison."""

    input_schema = NotEqualInput
    output_schema = NotEqualOutput
    description = "Return True if x != y"

    def compute(self, x: float, y: float) -> bool:
        """Return ``True`` if ``x`` is not equal to ``y``."""

        return x != y


class LessInput(BaseModel):
    """Input model for :class:`Less`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class LessOutput(BaseModel):
    """Output model for :class:`Less`."""

    result: bool = Field(..., description="Result of ``x < y``")

class Less(Computable):
    """Less-than comparison."""

    input_schema = LessInput
    output_schema = LessOutput
    description = "Return True if x < y"

    def compute(self, x: float, y: float) -> bool:
        """Return ``True`` if ``x`` is less than ``y``."""

        return x < y


class LessEqualInput(BaseModel):
    """Input model for :class:`LessEqual`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class LessEqualOutput(BaseModel):
    """Output model for :class:`LessEqual`."""

    result: bool = Field(..., description="Result of ``x <= y``")

class LessEqual(Computable):
    """Less-than-or-equal comparison."""

    input_schema = LessEqualInput
    output_schema = LessEqualOutput
    description = "Return True if x <= y"

    def compute(self, x: float, y: float) -> bool:
        """Return ``True`` if ``x`` is less than or equal to ``y``."""

        return x <= y


class GreaterInput(BaseModel):
    """Input model for :class:`Greater`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class GreaterOutput(BaseModel):
    """Output model for :class:`Greater`."""

    result: bool = Field(..., description="Result of ``x > y``")

class Greater(Computable):
    """Greater-than comparison."""

    input_schema = GreaterInput
    output_schema = GreaterOutput
    description = "Return True if x > y"

    def compute(self, x: float, y: float) -> bool:
        """Return ``True`` if ``x`` is greater than ``y``."""

        return x > y


class GreaterEqualInput(BaseModel):
    """Input model for :class:`GreaterEqual`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")

class GreaterEqualOutput(BaseModel):
    """Output model for :class:`GreaterEqual`."""

    result: bool = Field(..., description="Result of ``x >= y``")

class GreaterEqual(Computable):
    """Greater-than-or-equal comparison."""

    input_schema = GreaterEqualInput
    output_schema = GreaterEqualOutput
    description = "Return True if x >= y"

    def compute(self, x: float, y: float) -> bool:
        """Return ``True`` if ``x`` is greater than or equal to ``y``."""

        return x >= y


# Logical operations
class LogicalAndInput(BaseModel):
    """Input model for :class:`LogicalAnd`."""

    x: bool = Field(..., description="Left operand")
    y: bool = Field(..., description="Right operand")

class LogicalAndOutput(BaseModel):
    """Output model for :class:`LogicalAnd`."""

    result: bool = Field(..., description="Result of ``x and y``")

class LogicalAnd(Computable):
    """Logical AND operation."""

    input_schema = LogicalAndInput
    output_schema = LogicalAndOutput
    description = "Return x and y"

    def compute(self, x: bool, y: bool) -> bool:
        """Return logical AND of ``x`` and ``y``."""

        return x and y


class LogicalOrInput(BaseModel):
    """Input model for :class:`LogicalOr`."""

    x: bool = Field(..., description="Left operand")
    y: bool = Field(..., description="Right operand")

class LogicalOrOutput(BaseModel):
    """Output model for :class:`LogicalOr`."""

    result: bool = Field(..., description="Result of ``x or y``")

class LogicalOr(Computable):
    """Logical OR operation."""

    input_schema = LogicalOrInput
    output_schema = LogicalOrOutput
    description = "Return x or y"

    def compute(self, x: bool, y: bool) -> bool:
        """Return logical OR of ``x`` and ``y``."""

        return x or y


class LogicalNotInput(BaseModel):
    """Input model for :class:`LogicalNot`."""

    x: bool = Field(..., description="Value to invert")

class LogicalNotOutput(BaseModel):
    """Output model for :class:`LogicalNot`."""

    result: bool = Field(..., description="Logical negation of ``x``")

class LogicalNot(Computable):
    """Logical NOT operation."""

    input_schema = LogicalNotInput
    output_schema = LogicalNotOutput
    description = "Return not x"

    def compute(self, x: bool) -> bool:
        """Return logical NOT of ``x``."""

        return not x


# Unary operations
class NegateInput(BaseModel):
    """Input model for :class:`Negate`."""

    x: float = Field(..., description="Value to negate")

class NegateOutput(BaseModel):
    """Output model for :class:`Negate`."""

    result: float = Field(..., description="Negated value")

class Negate(Computable):
    """Negation operation."""

    input_schema = NegateInput
    output_schema = NegateOutput
    description = "Return -x"

    def compute(self, x: float) -> float:
        """Return the arithmetic negation of ``x``."""

        return -x


class InvertInput(BaseModel):
    """Input model for :class:`Invert`."""

    x: int = Field(..., description="Value to invert")

class InvertOutput(BaseModel):
    """Output model for :class:`Invert`."""

    result: int = Field(..., description="Bitwise inversion of ``x``")

class Invert(Computable):
    """Bitwise inversion."""

    input_schema = InvertInput
    output_schema = InvertOutput
    description = "Return bitwise inversion of x"

    def compute(self, x: int) -> int:
        """Return the bitwise inversion of ``x``."""

        return ~x

