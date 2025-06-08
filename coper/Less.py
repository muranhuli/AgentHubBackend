from core.Computable import Computable
from pydantic import BaseModel, Field


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
