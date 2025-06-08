from core.Computable import Computable
from pydantic import BaseModel, Field


class MinioReadInput(BaseModel):
    """Input model for :class:`MinioRead`."""

    bucket: str = Field(..., description="Bucket name")
    object_name: str = Field(..., description="Object key to read")


class MinioReadOutput(BaseModel):
    """Output model for :class:`MinioRead`."""

    data: bytes = Field(..., description="Retrieved data bytes")


class MinioRead(Computable):
    """Read data from a Minio bucket."""

    input_schema = MinioReadInput
    output_schema = MinioReadOutput
    description = "Read a file from Minio"

    def compute(self, bucket: str, object_name: str) -> bytes:
        """Read data from Minio and return it."""

        response = self.minio.get_object(bucket, object_name)
        try:
            data = response.read()
        finally:
            response.close()
        return data
