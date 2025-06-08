from core.Computable import Computable
from pydantic import BaseModel, Field


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
        """Return the bitwise XOR of ``x`` and ``y``.

        Args:
            x: Left operand.
            y: Right operand.

        Returns:
            Result of the operation.
        """

        return x ^ y
