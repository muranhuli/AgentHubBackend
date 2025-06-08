from core.Computable import Computable
from pydantic import BaseModel, Field


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
