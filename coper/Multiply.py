from core.Computable import Computable
from pydantic import BaseModel, Field


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
