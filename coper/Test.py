from core.Computable import Computable
from coper.Add import Add
from pydantic import BaseModel, Field


class TestInput(BaseModel):
    """Input model for :class:`Test`."""

    x: float = Field(..., description="First number")
    y: float = Field(..., description="Second number")


class TestOutput(BaseModel):
    """Output model for :class:`Test`."""

    result: float = Field(..., description="Computed result")

class Test(Computable):
    """Simple test operator calling :class:`Add`."""

    input_schema = TestInput
    output_schema = TestOutput
    description = "Add two numbers twice"

    def compute(self, x: float, y: float) -> float:
        """Use :class:`Add` twice to compute ``x + y`` twice."""

        add = Add()
        return add(x, y) + add(x, y)
