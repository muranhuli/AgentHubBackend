from core.Computable import Computable
from pydantic import BaseModel, Field


class AddInput(BaseModel):
    """Input model for :class:`Add`."""

    x: float = Field(..., description="First operand")
    y: float = Field(..., description="Second operand")


class AddOutput(BaseModel):
    """Output model for :class:`Add`."""

    result: float = Field(..., description="Sum of ``x`` and ``y``")


class Add(Computable):
    """Add two numbers."""

    input_schema = AddInput
    output_schema = AddOutput
    description = "Return the sum of two numbers"

    def compute(self, x: float, y: float) -> float:
        """Return the sum of ``x`` and ``y``.

        Args:
            x: First operand.
            y: Second operand.

        Returns:
            The calculated sum.
        """

        return x + y
