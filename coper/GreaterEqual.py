from core.Computable import Computable
from pydantic import BaseModel, Field


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
        """Return ``True`` if ``x`` is greater than or equal to ``y``.

        Args:
            x: Left operand.
            y: Right operand.

        Returns:
            Comparison result.
        """

        return x >= y
