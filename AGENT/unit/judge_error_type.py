import uuid
import re
import traceback
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
from AGENT.unit.pydantic_models import ErrorTypeAnalysisOutput
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
def judge_error_type(problem_desc: str, student_code: str,  llm_model: str) -> dict:
    """
    使用 LLM 判断学生的错误是概念性错误还是实现性错误。
    返回格式: {"error_type": "conceptual" 或 "implementation" 或 "unknown", "reasoning": "LLM 的分析", "raw_feedback": "原始评测信息"}
    """
    logging.info("🤖 LLM: 正在分析错误类型（概念性 vs 实现性）...")

    
    # 构建给 LLM 的 Prompt
    base_prompt = f"""
[SYSTEM]
你是一位顶级的竞赛编程导师。你将分析一个学生提交的、因逻辑错误而判为不正确的代码。
你的任务是根据问题陈述和学生代码，判断错误是源于核心算法/逻辑的缺陷（概念性错误），还是编码实现细节的失误（实现性错误）。

[问题陈述]
{problem_desc}

[学生代码]
```{SUBMISSION_LANGUAGE.lower()}
{student_code}
[任务]
分析学生代码，判断主要问题是出现在基本方法（概念性错误）还是代码的实现方式（实现性错误），并提供清晰的分类解释。
""" 
    structured_prompt = base_prompt + """
[输出要求]
你的输出必须是一个 JSON 对象，包含 error_type ('conceptual', 'implementation', 'unknown') 和 reasoning (详细解释) 两个键。
""" 
    natural_prompt = base_prompt + """
[输出格式]
请严格按照以下格式输出，不要添加任何额外内容：
错误类型: <conceptual 或 implementation>
原因分析: <你的详细解释>
"""
    try:
        llm = LLM(model=llm_model)
        error_type = "unknown"
        reasoning = "LLM 未能提供有效分析。"

        # === 主模式：尝试结构化输出 ===
        try:
            response = llm(structured_prompt, structured_output=ErrorTypeAnalysisOutput.model_json_schema()).result()
            structured_data = response.get("structured_output")

            if structured_data and "error_type" in structured_data and "reasoning" in structured_data:
                type_str = structured_data.get("error_type", "").lower()
                if type_str in ["conceptual", "implementation"]:
                    error_type = type_str
                reasoning = structured_data.get("reasoning")
                logging.info("✅ AI 已通过结构化输出分析错误类型。")

        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 将尝试自然语言解析方式...")

        # === 备用模式：如果主模式失败，则尝试自然语言解析 ===
        if error_type == "unknown":
            response = llm(natural_prompt).result()
            content = response.get("content", "")
            logging.debug(f"LLM 错误类型分析（自然语言）响应:\n{content}")
            
            error_type_match = re.search(r"错误类型:\s*(\w+)", content, re.IGNORECASE)
            reasoning_match = re.search(r"原因分析:\s*(.*)", content, re.DOTALL | re.IGNORECASE)
            
            if error_type_match:
                type_str = error_type_match.group(1).lower()
                if type_str in ["conceptual", "implementation"]:
                    error_type = type_str
            
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()
            
            if error_type != "unknown":
                logging.info("✅ AI 已通过自然语言解析分析错误类型。")
        
        # --- 构建并返回最终结果 ---
        logging.info(f"LLM 错误类型分类: {error_type.upper()}，原因: {reasoning[:100]}...")
        return {
            "error_type": error_type, 
            "reasoning": reasoning
        }

    except Exception as e:
        logging.error(f"❌ 使用 LLM 分析错误类型时发生严重错误: {e}")
        logging.error(traceback.format_exc())
        # 修正：移除了未定义的 'judge_info'
        return {
            "error_type": "unknown", 
            "reasoning": f"LLM 分析失败: {e}"
        }
