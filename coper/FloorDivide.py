from core.Computable import Computable
from pydantic import BaseModel, Field


class FloorDivideInput(BaseModel):
    """Input model for :class:`FloorDivide`."""

    x: float = Field(..., description="Dividend")
    y: float = Field(..., description="Divisor")


class FloorDivideOutput(BaseModel):
    """Output model for :class:`FloorDivide`."""

    result: float = Field(..., description="Result of ``x // y``")


class FloorDivide(Computable):
    """Floor division."""

    input_schema = FloorDivideInput
    output_schema = FloorDivideOutput
    description = "Return x // y"

    def compute(self, x: float, y: float) -> float:
        """Return ``x`` floor-divided by ``y``.

        Args:
            x: Dividend.
            y: Divisor.

        Returns:
            The floor division result.
        """

        return x // y
