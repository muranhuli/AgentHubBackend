from core.Computable import Computable
from pydantic import BaseModel, Field


class MinioDeleteInput(BaseModel):
    """Input model for :class:`MinioDelete`."""

    bucket: str = Field(..., description="Target bucket name")
    object_name: str = Field(..., description="Object key to delete")


class MinioDeleteOutput(BaseModel):
    """Output model for :class:`MinioDelete`."""

    result: bool = Field(..., description="Deletion status")


class MinioDelete(Computable):
    """Delete an object from a Minio bucket."""

    input_schema = MinioDeleteInput
    output_schema = MinioDeleteOutput
    description = "Delete a file from Minio"

    def compute(self, bucket: str, object_name: str) -> bool:
        """Delete an object from Minio and return ``True`` when done."""
        try:
            self.minio.remove_object(bucket, object_name)
        except Exception as e:
            raise Exception(f"Error deleting object {object_name} from bucket {bucket}: {e}")
        else:
            return True
