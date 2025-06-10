import uuid


from core.Context import Context
from coper.Minio import Minio


if __name__ == "__main__":

    with Context(task_id=str(uuid.uuid4())):
        
        # Test data
        test_bucket = "test-bucket"
        test_object = "test-file.txt"
        test_data = "Hello, Minio! This is a test file."
        
        minio = Minio()

        test_bucket = minio("make_bucket", test_bucket)
        
        # Test write operation
        print("Testing Minio write...")
        write_result = minio("write", test_bucket, test_object, test_data).result()
        print(f"Write result: {write_result}")
        
        # Test read operation
        print("Testing Minio read...")
        read_result = minio( "read", test_bucket, test_object).result()
        print(f"Read data: {read_result.decode('utf-8')}")
        
        # Verify data integrity
        if read_result.decode('utf-8') == test_data:
            print("✅ Minio read/write test passed!")
        else:
            print("❌ Minio read/write test failed!")
        
        # Test with bytes data
        print("\nTesting with bytes data...")
        bytes_data = b"Binary data test \x00\x01\x02"
        bytes_object = "test-binary.bin"

        minio("write", test_bucket, bytes_object, bytes_data)

        read_bytes = minio("read", test_bucket, bytes_object).result()
        
        if read_bytes == bytes_data:
            print("✅ Binary data test passed!")
        else:
            print("❌ Binary data test failed!")

        image_base64 = minio("read", test_bucket, 'test-binary.bin', "base64").result()
        print(f"Image Base64 data: {image_base64[:50]}...")