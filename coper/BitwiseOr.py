from core.Computable import Computable
from pydantic import BaseModel, Field


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
        """Return the bitwise OR of ``x`` and ``y``.

        Args:
            x: Left operand.
            y: Right operand.

        Returns:
            Result of the operation.
        """

        return x | y
