from core.Computable import Computable
from pydantic import BaseModel, Field


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
