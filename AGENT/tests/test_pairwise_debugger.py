# AGENT/tests/test_pairwise_debugger.py

import unittest
import uuid
from unittest.mock import patch, MagicMock

# 导入被测试的函数和所需的 Pydantic 模型
from AGENT.unit.pairwise_debugger import pairwise_testing_mode, TestCase
from core.Context import Context
import logging

class TestPairwiseDebugger(unittest.TestCase):
    """
    对 pairwise_debugger.py 模块进行单元测试。
    使用 mock 来隔离对 LLM, Sandbox, Minio 和用户输入的依赖。
    """

    def setUp(self):
        """为每个测试用例准备通用的测试数据。"""
        self.problem_details = {
            "full_markdown_description": "给定两个整数 a 和 b，计算它们的和。"
        }
        self.buggy_code = """
#include <iostream>
int main() {
    int a, b;
    std::cin >> a >> b;
    std::cout << a - b << std::endl; // Bug: should be a + b
    return 0;
}"""
        self.llm_model = "mock_model"
        self.language = "C++14"

    def test_ai_fix_and_success_flow(self):
        """
        测试一个完整的成功流程：
        1. 初始代码有bug。
        2. 对拍在第一个测试用例上失败。
        3. 模拟用户选择 '1' (AI自动修复)。
        4. AI "修复" 代码。
        5. 调试循环重新开始，使用新代码通过所有测试用例。
        """
        # 使用 Context 管理器，这对于依赖 get_context() 的代码是必需的
        with Context(task_id=f"test-{uuid.uuid4().hex}"):
            # 使用 patch 一次性模拟所有外部依赖
            with patch('AGENT.unit.pairwise_debugger.generate_brute_force_solution') as mock_brute_force, \
                 patch('AGENT.unit.pairwise_debugger.generate_edge_cases_with_llm') as mock_test_cases, \
                 patch('AGENT.unit.pairwise_debugger.run_code_in_sandbox') as mock_sandbox, \
                 patch('AGENT.unit.pairwise_debugger.debug_and_fix_with_llm') as mock_fix, \
                 patch('builtins.input', return_value='1') as mock_input:

                # --- 1. 配置 Mock 对象的行为 ---
                mock_brute_force.return_value = """
#include <iostream>
int main() { int a, b; std::cin >> a >> b; std::cout << a + b << std::endl; return 0; }
"""
                mock_test_cases.return_value = [
                    TestCase(input_data="3 5", expected_output="8", description="基础正数", case_type="basic"),
                    TestCase(input_data="-2 2", expected_output="0", description="正负数", case_type="boundary"),
                ]
                
                # 模拟AI修复后的代码
                fixed_code_by_ai = """
#include <iostream>
int main() {
    int a, b;
    std::cin >> a >> b;
    std::cout << a + b << std::endl; // FIX: Corrected subtraction to addition.
    return 0;
}
"""
                mock_fix.return_value = fixed_code_by_ai

                # 模拟沙箱的多次调用结果
                # 第一次循环 (失败): 暴力解正确, bug代码错误
                # 第二次循环 (成功): 暴力解正确, 修复后代码正确 (对两个用例)
                mock_sandbox.side_effect = [
                    '8',   # 1. 暴力解 on "3 5" -> 正确
                    '-2',  # 2. bug代码 on "3 5" -> 错误, 触发修复
                    # -- 循环重置 --
                    '8',   # 3. 暴力解 on "3 5" -> 正确
                    '8',   # 4. 修复后代码 on "3 5" -> 正确
                    '0',   # 5. 暴力解 on "-2 2" -> 正确
                    '0',   # 6. 修复后代码 on "-2 2" -> 正确
                ]

                # --- 2. 执行被测试的函数 ---
                pairwise_testing_mode(self.problem_details, self.buggy_code, self.llm_model, self.language)

                # --- 3. 断言：验证 Mock 是否按预期被调用 ---
                mock_brute_force.assert_called_once()
                mock_test_cases.assert_called_once()
                mock_input.assert_called_once()
                mock_fix.assert_called_once() # 确认AI修复被调用了一次

                # 验证debug_and_fix_with_llm的调用参数是否正确
                mock_fix.assert_called_with(
                    self.problem_details, 
                    self.buggy_code, 
                    "3 5",  # failed input
                    "8",    # expected output
                    "-2",   # actual output
                    self.language, 
                    self.llm_model
                )
                
                # 第一次失败循环(2次) + 第二次成功循环(4次) = 6次
                self.assertEqual(mock_sandbox.call_count, 6, 
                                 f"Expected 6 calls to sandbox, but got {mock_sandbox.call_count}")

if __name__ == '__main__':
    # 配置日志，以便在测试运行时看到输出
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(message)s')
    unittest.main()