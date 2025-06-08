from core.Computable import Computable
from pydantic import BaseModel, Field


class RightShiftInput(BaseModel):
    """Input model for :class:`RightShift`."""

    x: int = Field(..., description="Value to shift")
    y: int = Field(..., description="Number of bits")


class RightShiftOutput(BaseModel):
    """Output model for :class:`RightShift`."""

    result: int = Field(..., description="Result of ``x >> y``")


class RightShift(Computable):
    """Bitwise right shift."""

    input_schema = RightShiftInput
    output_schema = RightShiftOutput
    description = "Return x >> y"

    def compute(self, x: int, y: int) -> int:
        """Return ``x`` right-shifted by ``y`` bits."""

        return x >> y
