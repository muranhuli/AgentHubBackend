from io import BytesIO

from minio import S3Error

from core.Computable import Computable
from typing import Optional, Union
import base64
import os
from minio.deleteobjects import DeleteObject

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


class Minio(Computable):
    """Write data to a Minio bucket."""

    def make_bucket(self, bucket: str) -> str:
        """Create a bucket in Minio."""
        if not self.minio.bucket_exists(bucket):
            self.minio.make_bucket(bucket)
        return bucket

    def delete_bucket(self, bucket: str) -> str:
        """Delete a bucket in Minio."""
        if self.minio.bucket_exists(bucket):
            objects = self.minio.list_objects(bucket, recursive=True)
            delete_list = [DeleteObject(obj.object_name) for obj in objects]
            errors = self.minio.remove_objects(bucket, delete_list)
            err = "\n".join(f"{error.object_name}: {error.message}" for error in errors)
            if err:
                raise RuntimeError(f"Error deleting objects from bucket {bucket}: {err}")
            self.minio.remove_bucket(bucket)
        return bucket

    def write_s3(self, file: dict, data: bytes | str) -> dict:
        return self.writer(file['bucket'], file['object_name'], data)

    
    def writer(self, bucket: str, object_name: str, data: bytes | str) -> dict:
        """Write data to Minio and return ``True`` on success."""
        
        if isinstance(data, str):
            data = data.encode()
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("data must be bytes or str")
        self.minio.put_object(bucket, object_name, BytesIO(data), len(data))
        return {"bucket": bucket, "object_name": object_name}

    def read_s3(self, file: dict) -> Optional[Union[bytes, str]]:
        return self.read(file['bucket'], file['object_name'], output_format=file.get('output_format', 'bytes'))

    def read(self, bucket: str, object_name: str, output_format: str='bytes') -> Optional[Union[bytes, str]]:
        """Read data from Minio and return it."""

        try:
            self.minio.stat_object(bucket, object_name)
        except S3Error as exc:
            if exc.code == 'NoSuchKey':
                return None
            else:
                raise exc

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
        elif function_name == "read_s3":
            return self.read_s3(*args, **kwargs)
        elif function_name == "write_s3":
            return self.write_s3(*args, **kwargs)
        elif function_name == "delete":
            return self.delete(*args, **kwargs)
        elif function_name == "make_bucket":
            return self.make_bucket(*args, **kwargs)
        elif function_name == "delete_bucket":
            return self.delete_bucket(*args, **kwargs)
        else:
            raise ValueError(f"Unknown function name: {function_name}")
