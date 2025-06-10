from core.Computable import Computable
from pydantic import BaseModel, Field
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

class MinioReadBase64Input(BaseModel):
    """Input model for :class:`MinioRead`."""

    bucket: str = Field(..., description="Bucket name")
    object_name: str = Field(..., description="Object key to read")


class MinioReadBase64Output(BaseModel):
    """Output model for :class:`MinioRead`."""

    data_base64: str = Field(..., description="Retrieved data as base64 encoded string with data URL prefix")


class MinioReadBase64(Computable):
    """Read data from a Minio bucket."""

    input_schema = MinioReadBase64Input
    output_schema = MinioReadBase64Output
    description = "Read a file from Minio"

    def compute(self, bucket: str, object_name: str) -> str:
        """Read data from Minio and return it."""

        response = self.minio.get_object(bucket, object_name)
        try:
            data = response.read()
            data_base64 = base64.b64encode(data).decode('utf-8')
            # 根据文件类型添加正确的data URL前缀
            mime_type = get_image_mime_type(object_name)
            data_base64 = f"data:{mime_type};base64,{data_base64}"
        finally:
            response.close()
        return data_base64
