from core.Computable import Computable
from pydantic import BaseModel, Field


class EqualInput(BaseModel):
    """Input model for :class:`Equal`."""

    x: float = Field(..., description="Left operand")
    y: float = Field(..., description="Right operand")


class EqualOutput(BaseModel):
    """Output model for :class:`Equal`."""

    result: bool = Field(..., description="Result of ``x == y``")


class Equal(Computable):
    """Check equality."""

    input_schema = EqualInput
    output_schema = EqualOutput
    description = "Return True if x == y"

    def compute(self, x: float, y: float) -> bool:
        """Return ``True`` if ``x`` equals ``y``.

        Args:
            x: Left operand.
            y: Right operand.

        Returns:
            ``True`` if operands are equal otherwise ``False``.
        """

        return x == y
