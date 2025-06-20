import sys
import os
import uuid
import json
from paddleocr import PaddleOCR
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from core.Service import Service
from core.Context import Context
from coper.Minio import Minio

class OCRService(Service):
    """
    OCR服务，继承自 Service 类
    实现核心的 predict 方法，供外部调用
    参考：https://paddlepaddle.github.io/PaddleOCR/main/version3.x/pipeline_usage/OCR.html#22-python
    """

    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config = json.loads(open(config_path).read())
        super().__init__(config["service_id"])

    def initialize(self):
        self.ocr = PaddleOCR(
            use_doc_orientation_classify=False, # 通过 use_doc_orientation_classify 参数指定不使用文档方向分类模型
            use_doc_unwarping=False, # 通过 use_doc_unwarping 参数指定不使用文本图像矫正模型
            use_textline_orientation=False, # 通过 use_textline_orientation 参数指定不使用文本行方向分类模型
            device="gpu"
        )
        print("OCRSService initialized with PaddleOCR")
        
    def download_file(self, bucket: str, object_name: str):
        minio_client = Minio()
        result = minio_client.compute("read", bucket, object_name)
        if not result:
            raise FileNotFoundError(f"File not found in Minio: {bucket}/{object_name}")
        file_path = os.path.join("./tmp", object_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(result)
        return file_path
    
    def rm_file(self, file_path: str):
        """
        删除指定的文件
        :param file_path: 文件路径
        """
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} removed.")
        else:
            print(f"File {file_path} does not exist, cannot remove.")
    
    def ocr_predict(self, file_path: str):
        """
        使用 PaddleOCR 对指定文件进行 OCR 识别
        :param file_path: 文件路径
        :return: OCR 识别结果列表
        """
        print(f"Running OCR on file: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        result = self.ocr.predict(file_path)
        result = [res._to_json() for res in result]
        return result
    
    def compute(self, bucket: str, object_name: str):
        """
        处理 OCR 任务，下载文件并执行 OCR 识别
        :param bucket: Minio 存储桶名称
        :param object_name: Minio 对象名称
        :return: OCR 识别结果列表
        """
        file_path = self.download_file(bucket, object_name)
        try:
            result = self.ocr_predict(file_path)
        finally:
            self.rm_file(file_path)
        return result


# 示例调用
if __name__ == "__main__":
    with Context():
        service = OCRService()
        service.run()
