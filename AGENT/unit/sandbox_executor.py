# sandbox_executor.py (方案一：直接内部初始化)

import tempfile
import os
import shutil
import logging

from coper.Minio import Minio
from coper.Service import Service
from core.Utils import zip_directory_to_bytes, unzip_bytes_to_directory

# 配置保持不变
LANGUAGE_TO_SANDBOX_TEMPLATE = {
    "C++14": "gcc-13.3-cpp-std_14-O2",
    "C++17": "gcc-13.3-cpp-std_17-O2",
    "C++20": "gcc-13.3-cpp-std_20-O2",
    "Python3.11": "python-3.11",
    "Python3.12": "python-3.12",
}


def run_code_in_sandbox(code: str, input_data: str, language: str, bucket_name: str) -> str:
    """在沙箱中运行代码并返回其标准输出"""
    
    # --- 修改部分：在这里初始化 Service 和 Minio ---
    sandbox_service = Service("code-sandbox")
    minio_operator = Minio()

    lang_ext = ".cpp" if "C++" in language else ".py"
    source_filename = f"main{lang_ext}"
    sandbox_template = LANGUAGE_TO_SANDBOX_TEMPLATE.get(language)
    if not sandbox_template:
        return f"[ERROR] 不支持的沙箱语言: {language}"

    base_dir = tempfile.mkdtemp()
    source_dir = os.path.join(base_dir, "source")
    data_dir = os.path.join(base_dir, "data")

    try:
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        with open(os.path.join(source_dir, source_filename), "w", encoding="utf8") as f:
            f.write(code)
        with open(os.path.join(data_dir, "input"), "w", encoding="utf8") as f:
            f.write(input_data)

        source_zip = zip_directory_to_bytes(source_dir)
        data_zip = zip_directory_to_bytes(data_dir)

        source_io = minio_operator("write", bucket_name, "source.zip", source_zip).result()
        data_io = minio_operator("write", bucket_name, "data.zip", data_zip).result()

        res = sandbox_service(
            source_file=source_io, data_file=data_io,
            output_file={"bucket": bucket_name, "object_name": "output.zip"},
            execution_timeout=5, sandbox_template=sandbox_template
        ).result()

        if res.get('status') != 'success':
            return f"[SANDBOX_ERROR] {res.get('message', '未知沙箱错误')}"

        output_zip_bytes = minio_operator("read", bucket_name, "output.zip").result()
        if output_zip_bytes:
            output_dir_unzip = os.path.join(base_dir, "output")
            unzip_bytes_to_directory(output_zip_bytes, output_dir_unzip, overwrite=True)
            output_file_path = os.path.join(output_dir_unzip, "output")
            if os.path.exists(output_file_path):
                with open(output_file_path, "r", encoding="utf8") as f:
                    return f.read()
        return "[NO_OUTPUT]"
    finally:
        shutil.rmtree(base_dir)