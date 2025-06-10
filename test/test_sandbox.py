import os
import shutil
import tempfile
import uuid

from coper.Minio import Minio
from coper.Service import Service
from core.Context import Context
from core.Utils import zip_directory_to_bytes, unzip_bytes_to_directory

if __name__ == "__main__":
    task_id = str(uuid.uuid4())
    print("Task ID: {}".format(task_id))
    with Context(task_id=task_id):
        code_sandbox = Service("code-sandbox")

        cpp_source = """#include <bits/stdc++.h>
int main() {
    std::ios::sync_with_stdio(false);
    while(1);
    int a, b;
    if (!(std::cin >> a >> b)) return 1;
    std::cout << (a + b) << std::endl;
    return 0;
}
"""
        python_source = """import sys
def main():
    a, b = map(int, sys.stdin.read().strip().split())
    print(a + b)

if __name__ == "__main__":
    main()
"""
        base_dir = tempfile.mkdtemp()
        source_dir = os.path.join(base_dir, "source")
        data_dir = os.path.join(base_dir, "data")
        output_dir = os.path.join(base_dir, "output")
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # open(os.path.join(source_dir, "main.cc"), "w", encoding="utf8").write(cpp_source)
        open(os.path.join(source_dir, "main.py"), "w", encoding="utf8").write(python_source)
        open(os.path.join(data_dir, "input"), "w", encoding="utf8").write("3 4\n")
        source = zip_directory_to_bytes(source_dir)
        data = zip_directory_to_bytes(data_dir)

        io = Minio()

        bucket = io("make_bucket", "test-sandbox")


        source_io = io("write", bucket, "source.zip", source)
        data_io = io("write", bucket, "data.zip", data)

        res = code_sandbox(
            source_file=source_io,
            data_file=data_io,
            command_file=None,
            output_file={"bucket": bucket, "object_name": "output.zip"},
            execution_timeout=5,
            execution_memory=256,
            # sandbox_template="gcc-13.3-cpp-std_17-O2"
            sandbox_template="python-3.12"
        )

        res = res.result()
        print(res)

        output = io("read", bucket, "output.zip").result()
        if output:
            unzip_bytes_to_directory(output, output_dir)
            output_file = os.path.join(output_dir, "output")
            if os.path.exists(output_file):
               print("Output:", open(output_file, "r").read().strip())
            else:
                print("Output file does not exist.")
        else:
            print("No output received.")

        io("delete_bucket", bucket).result()

        shutil.rmtree(base_dir)




