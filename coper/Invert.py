from core.Computable import Computable
from pydantic import BaseModel, Field


class InvertInput(BaseModel):
    """Input model for :class:`Invert`."""

    x: int = Field(..., description="Value to invert")


class InvertOutput(BaseModel):
    """Output model for :class:`Invert`."""

    result: int = Field(..., description="Bitwise inversion of ``x``")


class Invert(Computable):
    """Bitwise inversion."""

    input_schema = InvertInput
    output_schema = InvertOutput
    description = "Return bitwise inversion of x"

    def compute(self, x: int) -> int:
        """Return the bitwise inversion of ``x``.

        Args:
            x: Value to invert.

        Returns:
            The inverted value.
        """

        return ~x
