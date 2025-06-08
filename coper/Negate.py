from core.Computable import Computable
from pydantic import BaseModel, Field


class NegateInput(BaseModel):
    """Input model for :class:`Negate`."""

    x: float = Field(..., description="Value to negate")


class NegateOutput(BaseModel):
    """Output model for :class:`Negate`."""

    result: float = Field(..., description="Negated value")


class Negate(Computable):
    """Negation operation."""

    input_schema = NegateInput
    output_schema = NegateOutput
    description = "Return -x"

    def compute(self, x: float) -> float:
        """Return the arithmetic negation of ``x``."""

        return -x