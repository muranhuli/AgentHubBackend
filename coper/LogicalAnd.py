from core.Computable import Computable
from pydantic import BaseModel, Field


class LogicalAndInput(BaseModel):
    """Input model for :class:`LogicalAnd`."""

    x: bool = Field(..., description="Left operand")
    y: bool = Field(..., description="Right operand")


class LogicalAndOutput(BaseModel):
    """Output model for :class:`LogicalAnd`."""

    result: bool = Field(..., description="Result of ``x and y``")


class LogicalAnd(Computable):
    """Logical AND operation."""

    input_schema = LogicalAndInput
    output_schema = LogicalAndOutput
    description = "Return x and y"

    def compute(self, x: bool, y: bool) -> bool:
        """Return logical AND of ``x`` and ``y``."""

        return x and y
