import uuid
from core.Context import Context
from coper.Service import Service


if __name__ == "__main__":
    from core.Context import Context
    with Context(task_id=str(uuid.uuid4())):
        ocr = Service("ocr-service")
        test_bucket = "test-bucket"
        test_object = "test_ocr.pdf"
        result = ocr(test_bucket, test_object).result()
        print(result)
        test_object = "test_ocr.jpg"
        result = ocr(test_bucket, test_object).result()
        print(result)
        