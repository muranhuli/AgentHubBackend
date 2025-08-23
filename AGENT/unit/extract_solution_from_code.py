import uuid
import re
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
from AGENT.unit.pydantic_models import SolutionDescriptionOutput
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
def extract_solution_from_code(code: str, problem_desc: str, model: str) -> dict:
    """
    从学生代码中提取解法描述
    返回格式: {"description": "解法描述", "code": "代码"}
    """
    base_prompt = f"""
[任务]
你是一个解法提取器，请从学生代码中提取解法描述。

[输入]
1. 问题描述:
{problem_desc}

2. 学生代码:
```{SUBMISSION_LANGUAGE.lower()}
{code}
"""
    structured_prompt = base_prompt + """
[要求]
提取解法的核心思路，包括使用的算法、数据结构、优化技巧等。
描述时间复杂度和空间复杂度。
语言简洁，不超过200字。
不要包含代码本身。
你的输出必须是一个只包含 "description" 键的 JSON 对象。
""" 
    natural_prompt = base_prompt + """
[要求]
提取解法的核心思路，包括使用的算法、数据结构、优化技巧等。
描述时间复杂度和空间复杂度。
语言简洁，不超过200字。
不要包含代码本身。
[输出格式]
请严格按照以下格式输出，不要添加任何额外内容：
解法描述: <你提取的描述文本>
"""
    try:
        llm = LLM(model=model)
        description = None

        # === 主模式：尝试结构化输出 ===
        try:
            response = llm(structured_prompt, structured_output=SolutionDescriptionOutput.model_json_schema()).result()
            structured_data = response.get("structured_output")

            if structured_data and "description" in structured_data:
                description = structured_data.get("description")
                logging.info("✅ AI 已通过结构化输出生成解法描述。")
        
        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 将尝试自然语言解析方式...")

        # === 备用模式：如果主模式失败，则尝试自然语言解析 ===
        if not description:
            response = llm(prompt=natural_prompt).result()
            content = response.get("content", "")
            logging.debug(f"AI 自然语言响应内容:\n{content}")
            
            desc_match = re.search(r'解法描述:\s*(.*)', content, re.DOTALL)
            if desc_match:
                description = desc_match.group(1).strip()
                logging.info("✅ AI 已通过自然语言解析生成解法描述。")

        # --- 构建并返回最终结果 ---
        if description:
            return {
                "description": description,
                "code": code
            }
        else:
            # 如果两种方式都失败
            logging.error("❌ 两种方式均未能提取到有效的解法描述。")
            return {"description": "未提取到解法描述", "code": code}

    except Exception as e:
        logging.error(f"❌ 提取解法时发生严重错误: {e}")
        logging.error(traceback.format_exc())
        return {"description": "解法提取失败", "code": code}
