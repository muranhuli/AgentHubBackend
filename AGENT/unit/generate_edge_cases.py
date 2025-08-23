import uuid
import re
import traceback
from typing import List, Union
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
from AGENT.unit.pydantic_models import TestCase, TestCaseList
log_filename = f"judge_error_type.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
SUBMISSION_LANGUAGE = "C++14"
def generate_edge_cases(problem_desc, model_identifier: str) -> str:
    """
    使用 LLM 根据题目描述生成潜在的边缘测试用例。
    返回格式化的边缘测试用例字符串。
    """
    # import traceback  # 添加必要的导入
    # import logging
    
    logging.info("🧪 LLM: 正在生成边缘测试用例...")

    base_prompt = f"""
[SYSTEM]
你是一位经验丰富的竞赛编程出题人和测试员。请根据给定的编程问题，生成一组全面的、可能暴露程序潜在缺陷的**边缘测试用例**。

[问题描述]
{problem_desc}
""" 
    structured_prompt = base_prompt + """
[任务]
请执行以下操作，并将结果以一个包含 'test_cases' 列表的 JSON 对象格式输出：
1.  仔细分析问题描述中的每一个约束条件。
2.  构思能够触及这些边界或极端情况的输入数据。
3.  对于每个测试用例，提供 `input_data`, `expected_output`, `description`, 和 `case_type` ('basic', 'boundary', 'edge')。
""" 
    natural_prompt = base_prompt + """
[任务]
请以清晰的 Markdown 格式列出这些边缘用例。对于每个用例，提供：
- 输入
- 预期输出
- 设计理由

示例：
## 边缘测试用例
### 用例 1: 最小值边界
- **输入**: ...
- **预期输出**: ...
- **设计理由**: ...
"""
    try:
        llm = LLM(model_identifier)

        # === 主模式：尝试结构化输出 ===
        try:
            response = llm(structured_prompt, structured_output=TestCaseList.model_json_schema()).result()
            structured_data = response.get("structured_output")

            if structured_data and "test_cases" in structured_data and isinstance(structured_data["test_cases"], list):
                test_cases_dicts = structured_data.get("test_cases", [])
                test_cases = [TestCase(**case_dict) for case_dict in test_cases_dicts]
                logging.info(f"✅ AI 已通过结构化输出生成 {len(test_cases)} 个测试用例。")
                return test_cases # 直接返回 TestCase 对象列表
        
        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 将尝试自然语言解析方式...")

        # === 备用模式：如果主模式失败，则获取 Markdown 字符串 ===
        logging.info("切换到自然语言模式生成边缘测试用例...")
        response = llm(natural_prompt).result()
        content = response.get("content", "")
        logging.debug(f"LLM 边缘测试用例（自然语言）响应:\n{content}")
        
        edge_cases_content = content.strip()
        if not edge_cases_content.startswith("#"):
            edge_cases_content = f"# 边缘测试用例\n\n{edge_cases_content}"
            
        logging.info("✅ AI 已通过自然语言格式生成测试用例报告。")
        return edge_cases_content

    except Exception as e:
        logging.error(f"❌ 生成边缘测试用例时发生严重错误: {e}")
        logging.error(traceback.format_exc())
        return "# 边缘测试用例\n\n生成失败，请手动检查。"
