from core.Computable import Computable
from pydantic import BaseModel, Field


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
        """Return the bitwise AND of ``x`` and ``y``.

        Args:
            x: Left operand.
            y: Right operand.

        Returns:
            Result of the operation.
        """

        return x & y
