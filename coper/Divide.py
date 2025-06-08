from core.Computable import Computable
from pydantic import BaseModel, Field


class DivideInput(BaseModel):
    """Input model for :class:`Divide`."""

    x: float = Field(..., description="Dividend")
    y: float = Field(..., description="Divisor")


class DivideOutput(BaseModel):
    """Output model for :class:`Divide`."""

    result: float = Field(..., description="Quotient of ``x / y``")


class Divide(Computable):
    """Division operation."""

    input_schema = DivideInput
    output_schema = DivideOutput
    description = "Return x divided by y"

    def compute(self, x: float, y: float) -> float:
        """Return ``x`` divided by ``y``.

        Args:
            x: Dividend.
            y: Divisor.

        Returns:
            The quotient.
        """

        return x / y
