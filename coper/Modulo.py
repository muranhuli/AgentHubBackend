from core.Computable import Computable
from pydantic import BaseModel, Field


class ModuloInput(BaseModel):
    """Input model for :class:`Modulo`."""

    x: float = Field(..., description="Dividend")
    y: float = Field(..., description="Divisor")


class ModuloOutput(BaseModel):
    """Output model for :class:`Modulo`."""

    result: float = Field(..., description="Result of ``x % y``")


class Modulo(Computable):
    """Modulo operation."""

    input_schema = ModuloInput
    output_schema = ModuloOutput
    description = "Return x % y"

    def compute(self, x: float, y: float) -> float:
        """Return the remainder of ``x`` divided by ``y``."""

        return x % y
