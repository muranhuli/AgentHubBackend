from io import BytesIO

from core.Computable import Computable
from pydantic import BaseModel, Field
from typing import Optional, Union
import base64
import os

def get_image_mime_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp'
    }
    return mime_types.get(ext, 'image/jpeg')  # 默认为jpeg

class MinioInput(BaseModel):
    """Input model for Minio operations."""
    
    function_name: str = Field(..., description="Function to execute (write, read, delete)")
    bucket: str = Field(..., description="Bucket name")
    object_name: str = Field(..., description="Object key")
    data: bytes | str = Field(..., description="Data to write or read")
    output_format: Optional[str] = Field(default='bytes', description="Output format for read operation (bytes or base64)")

class MinioOutput(BaseModel):
    """Output model for Minio operations."""
    
    result: bool = Field(..., description="Write status for write operation")
    data: Optional[Union[bytes, str]] = Field(default=None, description="Data read from Minio (if applicable)")


class Minio(Computable):
    """Write data to a Minio bucket."""

    input_schema = MinioInput
    output_schema = MinioOutput
    description = "Write a file to Minio"

    def make_bucket(self, bucket: str) -> str:
        """Create a bucket in Minio."""
        if not self.minio.bucket_exists(bucket):
            self.minio.make_bucket(bucket)
        return bucket
    
    def writer(self, bucket: str, object_name: str, data: bytes | str) -> dict:
        """Write data to Minio and return ``True`` on success."""
        
        if isinstance(data, str):
            data = data.encode()
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("data must be bytes or str")
        self.minio.put_object(bucket, object_name, BytesIO(data), len(data))
        return {"bucket": bucket, "object_name": object_name}

    def read(self, bucket: str, object_name: str, output_format: str='bytes') -> Optional[Union[bytes, str]]:
        """Read data from Minio and return it."""
        response = self.minio.get_object(bucket, object_name)
        try:
            data = response.read()
            if output_format == 'bytes':
                pass
            elif output_format == 'base64':
                data = base64.b64encode(data).decode('utf-8')
                mime_type = get_image_mime_type(object_name)
                data = f"data:{mime_type};base64,{data}"
            return data
        finally:
            response.close()


    def delete(self, bucket: str, object_name: str) -> dict:
        """Delete an object from Minio and return ``True`` when done."""
        try:
            self.minio.remove_object(bucket, object_name)
        except Exception as e:
            raise Exception(f"Error deleting object {object_name} from bucket {bucket}: {e}")
        else:
            return {"bucket": bucket, "object_name": object_name}

    def compute(self, function_name: str, *args, **kwargs) -> Optional[Union[bool, bytes, str, dict]]:
        """Execute the specified function and return the result."""
        if function_name == "write":
            return self.writer(*args, **kwargs)
        elif function_name == "read":
            return self.read(*args, **kwargs)
        elif function_name == "delete":
            return self.delete(*args, **kwargs)
        elif function_name == "make_bucket":
            return self.make_bucket(*args, **kwargs)
        else:
            raise ValueError(f"Unknown function name: {function_name}")
