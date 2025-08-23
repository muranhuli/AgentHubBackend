from AGENT.unit.debug_and_fix import debug_and_fix
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
if __name__ == '__main__':
    with Context(router="1234567890", task_id="test_debug_and_fix"):
        problem_details = {
    "full_markdown_description": "创建整数数组"
}
        buggy_code = """
int* create_array(int size) {
    int* arr = new int[size];
    return arr;  // 错误：没有提供释放内存的方法
}
"""
        failed_case_input = "size=10"
        expected_output = "数组指针"
        actual_output = "内存泄漏"
        language = "C++"
        model = "volcengine/doubao-seed-1-6-250615"
        user_hint = "需要解决内存泄漏问题"

# 预期输出（模拟 LLM 返回）
        expected_fixed_code = """
int* create_array(int size) {
    int* arr = new int[size];
    return arr;
}

// 添加释放内存的函数
void delete_array(int* arr) {
    delete[] arr;
}
"""     
        result = debug_and_fix(problem_details, buggy_code, failed_case_input, expected_output, actual_output, language, model, user_hint)
        print(result)