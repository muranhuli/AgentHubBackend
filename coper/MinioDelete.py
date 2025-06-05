from core.Computable import Computable


class MinioDelete(Computable):
    """Delete an object from a Minio bucket."""

    def compute(self, bucket: str, object_name: str):
        self.minio.remove_object(bucket, object_name)
        return True
