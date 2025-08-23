#!/usr/bin/env python3
"""
智能测试用例生成器
Intelligent Test Case Generator

根据题目描述自动生成测试用例，包括：
- 基础测试用例
- 边界情况测试
- 错误处理测试
- 性能测试用例
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging
import uuid
from pydantic import BaseModel, Field

from coper.LLM import LLM
from core.Computable import Computable

# --- 数据结构定义 ---

@dataclass
class TestCase:
    """测试用例数据结构"""
    input_data: str
    expected_output: str
    description: str
    case_type: str  # "basic", "boundary", "edge"


# --- 可计算算子定义 ---

class TestCaseGenerator(Computable):
    """
    【已改造】一个 Computable 算子，用于智能生成测试用例。
    它封装了传统的模板方法和LLM增强方法，并可以在 Runner 进程中被异步调用。
    """
    
    # 为 Computable 定义输入输出 schema
    class Input(BaseModel):
        problem_text: str = Field(..., description="The full markdown description of the problem.")
        use_llm: bool = Field(default=True, description="Whether to use LLM enhancement.")

    class Output(BaseModel):
        test_cases: List[Dict] = Field(..., description="A list of generated test cases.")

    input_schema = Input
    output_schema = Output
    description = "Generates test cases for a programming problem, with optional LLM enhancement."
    
    def __init__(self):
        super().__init__()
        # 传统模式匹配方法
        self.problem_patterns = {
            "求和": self._generate_sum_cases, "加法": self._generate_sum_cases, "相加": self._generate_sum_cases,
            "求积": self._generate_product_cases, "乘法": self._generate_product_cases, "相乘": self._generate_product_cases,
            "最大值": self._generate_max_cases, "最小值": self._generate_min_cases,
            "排序": self._generate_generic_cases, "查找": self._generate_generic_cases,
            "斐波那契": self._generate_fibonacci_cases, "阶乘": self._generate_factorial_cases,
            "素数": self._generate_prime_cases, "回文": self._generate_palindrome_cases,
        }
        logging.basicConfig(level=logging.INFO)

    def compute(self, problem_text: str, use_llm: bool = True) -> Dict[str, List[Dict]]:
        """
        这是算子的执行入口，由 Runner 进程调用。
        """
        problem_type = self._identify_problem_type(problem_text)
        
        generator_func = self.problem_patterns.get(problem_type, self._generate_generic_cases)
        traditional_cases = generator_func(problem_text)
        
        if use_llm:
            try:
                llm_cases = self._generate_with_llm_sync(problem_text, problem_type)
                merged_cases = self._merge_test_cases(traditional_cases, llm_cases)
                return {"test_cases": [asdict(case) for case in merged_cases]}
            except Exception as e:
                logging.warning(f"LLM生成失败，将仅使用传统方法: {str(e)}")
                return {"test_cases": [asdict(case) for case in traditional_cases]}
        else:
            return {"test_cases": [asdict(case) for case in traditional_cases]}

    def _generate_with_llm_sync(self, problem_text: str, problem_type: str) -> List[TestCase]:
        """
        在 Runner 进程内部，同步调用 LLM 算子来生成测试用例。
        """
        prompt = self._build_llm_prompt(problem_text, problem_type)
        
        TestCaseSchema = {
            "title": "TestCases",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "input_data": {"type": "string", "description": "Test case input data."},
                    "expected_output": {"type": "string", "description": "Expected output for the input."},
                    "description": {"type": "string", "description": "A brief description of the test case."},
                    "case_type": {"type": "string", "enum": ["basic", "boundary", "edge"], "description": "The type of the test case."}
                },
                "required": ["input_data", "expected_output", "description", "case_type"]
            }
        }
        
        # 实例化LLM算子。因为它是在一个已有的Context中被调用的，所以无需再次创建Context。
        llm = LLM("volcengine/doubao-seed-1-6-flash-250615", custom_provider="volcengine")
        
        # 直接调用LLM的compute方法，因为它在Runner进程中已经是同步执行的
        response = llm.compute(prompt, structured_output=TestCaseSchema)
        llm_results = response.get("structured_output", [])

        if not llm_results:
            logging.warning("LLM 未能返回有效的测试用例列表。")
            return []
            
        test_cases = []
        for result in llm_results:
            try:
                # 使用字典解包来创建 TestCase 实例
                test_cases.append(TestCase(**result))
            except TypeError as e:
                logging.warning(f"解析LLM返回的单个测试用例失败: {result}, 错误: {e}")
                continue
        return test_cases

    def _build_llm_prompt(self, problem_text: str, problem_type: str) -> str:
        """构建发送给 LLM 的提示词"""
        return f"""
请为以下编程题目生成测试用例：

题目描述：
{problem_text}

题目类型：{problem_type}

请生成以下类型的测试用例：
1. 基础测试用例（basic）：正常情况下的典型输入
2. 边界测试用例（boundary）：边界条件和特殊情况
3. 极值测试用例（edge）：极大值、极小值等极端情况

请严格按照JSON数组格式返回，不要包含任何其他文字或解释。
格式示例:
[
  {{
    "input_data": "输入数据",
    "expected_output": "期望输出",
    "description": "测试用例描述",
    "case_type": "basic"
  }}
]
"""

    def _merge_test_cases(self, traditional_cases: List[TestCase], llm_cases: List[TestCase]) -> List[TestCase]:
        """合并传统方法和LLM生成的测试用例，去重并优化"""
        merged_cases: List[TestCase] = []
        seen_inputs = set()
        
        for case in llm_cases + traditional_cases:
            if case.input_data not in seen_inputs:
                merged_cases.append(case)
                seen_inputs.add(case.input_data)
        
        return merged_cases
    
    def _identify_problem_type(self, problem_text: str) -> str:
        """识别题目类型"""
        # ... (此方法保持不变) ...
        text_lower = problem_text.lower()
        if "和" in problem_text or "相加" in text_lower or "加法" in text_lower: return "求和"
        if "积" in problem_text or "相乘" in text_lower or "乘法" in text_lower: return "求积"
        if "最大" in problem_text: return "最大值"
        if "最小" in problem_text: return "最小值"
        if "阶乘" in problem_text: return "阶乘"
        if "素数" in problem_text: return "素数"
        if "斐波那契" in problem_text: return "斐波那契"
        if "回文" in problem_text: return "回文"
        for pattern in self.problem_patterns.keys():
            if pattern in text_lower or pattern in problem_text: return pattern
        return "通用"

    # --- 以下所有 _generate_..._cases 方法都保持不变 ---
    def _generate_sum_cases(self, problem_text: str) -> List[TestCase]:
        return [
            TestCase("1 2", "3", "基础正数相加", "basic"), TestCase("5 7", "12", "基础正数相加", "basic"),
            TestCase("0 0", "0", "零值测试", "boundary"), TestCase("0 5", "5", "一个数为零", "boundary"),
            TestCase("-3 3", "0", "正负数相加为零", "boundary"), TestCase("-5 -7", "-12", "负数相加", "boundary"),
            TestCase("1000000 2000000", "3000000", "大数相加", "edge"),
        ]
    
    # ... (此处省略其他 _generate_..._cases 函数的重复代码，它们都保持不变) ...
    def _generate_product_cases(self, problem_text: str) -> List[TestCase]:
        return [TestCase("2 3", "6", "基础正数相乘", "basic"), TestCase("0 5", "0", "乘数为零", "boundary")]
    def _generate_max_cases(self, problem_text: str) -> List[TestCase]:
        return [TestCase("3 7", "7", "两个正数比较", "basic"), TestCase("5 5", "5", "相等数字", "boundary")]
    def _generate_min_cases(self, problem_text: str) -> List[TestCase]:
        return [TestCase("3 7", "3", "两个正数比较", "basic"), TestCase("5 5", "5", "相等数字", "boundary")]
    def _generate_factorial_cases(self, problem_text: str) -> List[TestCase]:
        return [TestCase("3", "6", "3的阶乘", "basic"), TestCase("0", "1", "0的阶乘", "boundary")]
    def _generate_fibonacci_cases(self, problem_text: str) -> List[TestCase]:
        return [TestCase("5", "5", "第5个斐波那契数", "basic"), TestCase("0", "0", "第0个斐波那契数", "boundary")]
    def _generate_prime_cases(self, problem_text: str) -> List[TestCase]:
        return [TestCase("7", "是素数", "小素数", "basic"), TestCase("1", "不是素数", "1不是素数", "boundary")]
    def _generate_palindrome_cases(self, problem_text: str) -> List[TestCase]:
        return [TestCase("aba", "是回文", "字符串回文", "basic"), TestCase("", "是回文", "空字符串", "boundary")]
    def _generate_generic_cases(self, problem_text: str) -> List[TestCase]:
        return [TestCase("1", "1", "基础测试1", "basic"), TestCase("0", "0", "零值测试", "boundary")]


# --- 辅助函数，用于格式化输出 ---
def format_test_cases(test_cases: List[TestCase]) -> str:
    """格式化测试用例为可读文本"""
    output = ["🧪 智能生成的测试用例"]
    output.append("=" * 60)
    case_groups = {}
    for case in test_cases:
        case_groups.setdefault(case.case_type, []).append(case)
    
    type_names = { "basic": "📝 基础用例", "boundary": "🎯 边界用例", "edge": "⚡ 极值用例" }
    for case_type, cases in case_groups.items():
        output.append(f"\n{type_names.get(case_type, case_type)}:")
        for i, case in enumerate(cases, 1):
            output.append(f"  {i}. {case.description} -> 输入: `{case.input_data}`, 输出: `{case.expected_output}`")
    return "\n".join(output)


# --- 独立的测试函数 (可选) ---
def standalone_test():
    """用于独立测试 TestCaseGenerator 算子的函数"""
    problem = "编写一个程序，输入两个整数，输出它们的和。"
    print(f"📝 正在为问题生成测试用例:\n{problem}\n")

    # 必须在 Context 中调用算子
    with Context(task_id="standalone-test"):
        generator = TestCaseGenerator()
        # 调用算子，它返回一个 future
        future = generator(problem_text=problem, use_llm=True)
        # 获取结果
        print("⏳ 正在等待 Runner 执行任务...")
        result = future.result()
        print("✅ 任务执行完成！")

        # 将结果从字典转换回 TestCase 对象
        test_cases_data = result.get('test_cases', [])
        test_cases = [TestCase(**data) for data in test_cases_data]

        # 格式化并打印
        print(format_test_cases(test_cases))

if __name__ == "__main__":
    # 运行此文件将执行一个独立的测试
    # 前提是必须先在另一个终端启动 core/Runner.py
    standalone_test()