from io import BytesIO

from core.Computable import Computable
from pydantic import BaseModel, Field


class MinioWriteInput(BaseModel):
    """Input model for :class:`MinioWrite`."""

    bucket: str = Field(..., description="Bucket name")
    object_name: str = Field(..., description="Object key")
    data: bytes | str = Field(..., description="Data to write")


class MinioWriteOutput(BaseModel):
    """Output model for :class:`MinioWrite`."""

    result: bool = Field(..., description="Write status")


class MinioWrite(Computable):
    """Write data to a Minio bucket."""

    input_schema = MinioWriteInput
    output_schema = MinioWriteOutput
    description = "Write a file to Minio"

    def compute(self, bucket: str, object_name: str, data: bytes | str) -> bool:
        """Write data to Minio and return ``True`` on success."""

        if isinstance(data, str):
            data = data.encode()
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("data must be bytes or str")
        if not self.minio.bucket_exists(bucket):
            self.minio.make_bucket(bucket)
        self.minio.put_object(bucket, object_name, BytesIO(data), len(data))
        return True
