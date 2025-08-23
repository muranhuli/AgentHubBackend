import uuid
import re
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import traceback
import logging
from AGENT.unit.pydantic_models import PossibleErrorsOutput
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
def generate_possible_errors(problem_desc, model_name: str) -> str:
    """
    生成针对特定题目可能出现的错误类型和具体描述。
    
    :param problem_description: 题目描述（简化或完整描述）
    :param model_name: 使用的LLM模型名称
    :return: 错误描述的Markdown文本
    """
    logging.info("🔍 LLM: 正在生成潜在错误分析...")
    
    # 构建提示词
    base_prompt = f"""
[SYSTEM]
你是一位经验丰富的竞赛编程教练，请分析给定编程问题，指出解题者在用 {SUBMISSION_LANGUAGE} 解决此问题时可能犯的常见错误类型及具体原因。

[问题描述]
{problem_desc}
""" 
    structured_prompt = base_prompt + """
[任务]
请执行以下操作，并将结果以 Markdown 格式填充到指定的 JSON 字段 `markdown_content` 中：
1. 分析题目中的主要难点和陷阱。
2. 分类列出可能的错误类型（如概念性错误、实现性错误）。
3. 为每种错误类型提供简要的示例、原因解释和避免建议。
"""
    natural_prompt = base_prompt + """
[任务]
请以清晰的 Markdown 格式输出你的分析报告，必须包含以下部分：
1. **主要难点与陷阱**
2. **概念性错误** (如果适用)
3. **实现性错误** (如果适用)
   - 错误1描述
     - 示例代码/伪代码
     - 原因分析
     - 避免建议
"""
    try:
        llm = LLM(model_name)
        errors_content = None

        # === 主模式：尝试结构化输出 ===
        try:
            response = llm(structured_prompt, structured_output=PossibleErrorsOutput.model_json_schema()).result()
            structured_data = response.get("structured_output")

            if structured_data and "markdown_content" in structured_data:
                errors_content = structured_data.get("markdown_content")
                logging.info("✅ AI 已通过结构化输出生成潜在错误分析。")
        
        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 将尝试自然语言解析方式...")

        # === 备用模式：如果主模式失败，则获取自然语言输出 ===
        if not errors_content:
            response = llm(natural_prompt).result()
            content = response.get("content", "")
            logging.debug(f"LLM 潜在错误分析（自然语言）响应:\n{content}")
            errors_content = content.strip()
            if errors_content:
                logging.info("✅ AI 已通过自然语言格式生成潜在错误分析。")
        
        # --- 构建并返回最终报告 ---
        if not errors_content:
            errors_content = "LLM 未能生成有效的潜在错误分析。"
        
        # 确保报告有一个统一的标题
        if not errors_content.strip().startswith("#"):
            errors_content = f"# 潜在错误分析\n\n{errors_content}"

        return errors_content

    except Exception as e:
        logging.error(f"❌ 生成潜在错误分析时发生严重错误: {e}")
        logging.error(traceback.format_exc())
        return "# 潜在错误分析\n\n生成失败，请手动分析题目难点和常见错误。"