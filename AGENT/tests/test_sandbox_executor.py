# test_sandbox_executor.py

import uuid
from coper.Minio import Minio
from coper.Service import Service
from core.Context import get_context, Context
from AGENT.unit.sandbox_executor import run_code_in_sandbox
import logging

if __name__ == '__main__':
    # 使用一个唯一的 task_id，并指定 router
    with Context(router="1234567890", task_id=f"test-sandbox-executor-{uuid.uuid4().hex}"):
        print("--- 准备测试 sandbox_executor.py ---")

        # --- 准备测试数据 ---
        cpp_code = """
#include <iostream>
#include <string>
#include <vector>
#include <numeric>
#include <algorithm>

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);
    int a, b;
    if (!(std::cin >> a >> b)) {
        return 1;
    }
    std::cout << a + b << std::endl;
    return 0;
}
"""
        python_code = """
import sys
try:
    a, b = map(int, sys.stdin.readline().split())
    print(a + b)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
"""
        input_data = "123 456"
        expected_output = "579"

        # 为了隔离，每次测试都创建一个新的 bucket
        ctx = get_context()
        minio_client = ctx.minio
        bucket_name = f"test-sandbox-{str(uuid.uuid4())[:8]}"

        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
        print(f"✅ 成功创建临时 Minio 存储桶: {bucket_name}")

        # --- 测试 C++ 代码 ---
        print("\n--- 正在测试 C++ 代码 ---")
        cpp_result = run_code_in_sandbox(
            cpp_code,
            input_data, 
            "C++14", 
            bucket_name
        )
        print(f"C++ 代码输入:\n{input_data}")
        print(f"C++ 代码输出: {cpp_result.strip()}")
        print(f"预期输出: {expected_output}")
        if cpp_result.strip() == expected_output:
            print("✅ C++ 测试通过！")
        else:
            print("❌ C++ 测试失败！")

        # --- 测试 Python 代码 ---
        print("\n--- 正在测试 Python 代码 ---")
        python_result = run_code_in_sandbox(
            python_code,
            input_data, 
            "Python3.11", 
            bucket_name
        )
        print(f"Python 代码输入:\n{input_data}")
        print(f"Python 代码输出: {python_result.strip()}")
        print(f"预期输出: {expected_output}")
        if python_result.strip() == expected_output:
            print("✅ Python 测试通过！")
        else:
            print("❌ Python 测试失败！")

        