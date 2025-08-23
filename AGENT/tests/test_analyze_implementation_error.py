from AGENT.unit.analyze_implementation_error import analyze_implementation_error

from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
if __name__ == '__main__':
    with Context(router="1234567890", task_id="test_judge_error_type"):
        problem_desc = """
问题：实现两个超大数的加法（长度≤1000位）
输入：两个字符串 a="12345678901234567890" b="98765432109876543210"
输出：返回它们相加后的字符串
注意：不能直接用类型转换，需手工实现进位逻辑
"""

        student_code = """
def add_big_numbers(a: str, b: str) -> str:
    result = []
    carry = 0
    i, j = len(a)-1, len(b)-1
    
    # 存在漏洞的循环
    while i >= 0 and j >= 0:
        digit_sum = int(a[i]) + int(b[j]) + carry
        carry = digit_sum // 10
        result.append(str(digit_sum % 10))
        i -= 1
        j -= 1
    
    # 未处理剩余位数
    return ''.join(result[::-1])
"""

        error_analysis = {
    "error_type": "implementation",
    "reasoning": "学生代码核心算法正确但未处理长度不同的数。当两数位数不同时，仅处理了公共长度部分，剩余高位数字被丢弃"
}

        result = analyze_implementation_error(problem_desc, student_code, error_analysis, "volcengine/doubao-seed-1-6-250615")
        print(result)