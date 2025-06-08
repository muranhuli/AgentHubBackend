from core.Computable import Computable
from pydantic import BaseModel, Field


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
