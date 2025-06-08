from core.Computable import Computable
from pydantic import BaseModel, Field


class LogicalOrInput(BaseModel):
    """Input model for :class:`LogicalOr`."""

    x: bool = Field(..., description="Left operand")
    y: bool = Field(..., description="Right operand")


class LogicalOrOutput(BaseModel):
    """Output model for :class:`LogicalOr`."""

    result: bool = Field(..., description="Result of ``x or y``")


class LogicalOr(Computable):
    """Logical OR operation."""

    input_schema = LogicalOrInput
    output_schema = LogicalOrOutput
    description = "Return x or y"

    def compute(self, x: bool, y: bool) -> bool:
        """Return logical OR of ``x`` and ``y``."""

        return x or y
