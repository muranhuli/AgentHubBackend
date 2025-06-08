from core.Computable import Computable
from pydantic import BaseModel, Field


class LeftShiftInput(BaseModel):
    """Input model for :class:`LeftShift`."""

    x: int = Field(..., description="Value to shift")
    y: int = Field(..., description="Number of bits")


class LeftShiftOutput(BaseModel):
    """Output model for :class:`LeftShift`."""

    result: int = Field(..., description="Result of ``x << y``")


class LeftShift(Computable):
    """Bitwise left shift."""

    input_schema = LeftShiftInput
    output_schema = LeftShiftOutput
    description = "Return x << y"

    def compute(self, x: int, y: int) -> int:
        """Return ``x`` left-shifted by ``y`` bits."""

        return x << y
