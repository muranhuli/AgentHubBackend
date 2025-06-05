from core.Computable import Computable


class MinioRead(Computable):
    """Read data from a Minio bucket."""

    def compute(self, bucket: str, object_name: str):
        response = self.minio.get_object(bucket, object_name)
        try:
            data = response.read()
        finally:
            response.close()
        return data
