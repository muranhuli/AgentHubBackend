from core.Computable import Computable
from pydantic import BaseModel, Field


class GreaterInput(BaseModel):
    """Input model for :class:`Greater`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")


class GreaterOutput(BaseModel):
    """Output model for :class:`Greater`."""

    result: bool = Field(..., description="Result of ``x > y``")


class Greater(Computable):
    """Greater-than comparison."""

    input_schema = GreaterInput
    output_schema = GreaterOutput
    description = "Return True if x > y"

    def compute(self, x: float, y: float) -> bool:
        """Return ``True`` if ``x`` is greater than ``y``.

        Args:
            x: Left operand.
            y: Right operand.

        Returns:
            Comparison result.
        """

        return x > y
