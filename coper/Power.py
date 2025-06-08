from core.Computable import Computable
from pydantic import BaseModel, Field


class PowerInput(BaseModel):
    """Input model for :class:`Power`."""

    x: float = Field(..., description="Base value")
    y: float = Field(..., description="Exponent")


class PowerOutput(BaseModel):
    """Output model for :class:`Power`."""

    result: float = Field(..., description="Result of ``x ** y``")


class Power(Computable):
    """Exponentiation operation."""

    input_schema = PowerInput
    output_schema = PowerOutput
    description = "Return x ** y"

    def compute(self, x: float, y: float) -> float:
        """Return ``x`` raised to the ``y`` power."""

        return x ** y
