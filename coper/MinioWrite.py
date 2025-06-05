from io import BytesIO

from core.Computable import Computable


class MinioWrite(Computable):
    """Write data to a Minio bucket."""

    def compute(self, bucket: str, object_name: str, data):
        if isinstance(data, str):
            data = data.encode()
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("data must be bytes or str")
        if not self.minio.bucket_exists(bucket):
            self.minio.make_bucket(bucket)
        self.minio.put_object(bucket, object_name, BytesIO(data), len(data))
        return True
