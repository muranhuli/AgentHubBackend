from core.Computable import Computable
from pydantic import BaseModel, Field


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