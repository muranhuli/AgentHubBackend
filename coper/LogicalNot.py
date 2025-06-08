from core.Computable import Computable
from pydantic import BaseModel, Field


class LogicalNotInput(BaseModel):
    """Input model for :class:`LogicalNot`."""

    x: bool = Field(..., description="Value to invert")


class LogicalNotOutput(BaseModel):
    """Output model for :class:`LogicalNot`."""

    result: bool = Field(..., description="Logical negation of ``x``")


class LogicalNot(Computable):
    """Logical NOT operation."""

    input_schema = LogicalNotInput
    output_schema = LogicalNotOutput
    description = "Return not x"

    def compute(self, x: bool) -> bool:
        """Return logical NOT of ``x``."""

        return not x
