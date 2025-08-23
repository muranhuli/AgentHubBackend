# 修改SUBMISSION_LANGUAGE使之作为参数传递

import uuid
import re
import traceback
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
from AGENT.unit.pydantic_models import ImplementationAnalysisOutput
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
def analyze_implementation_error(problem_desc: str, student_code: str, error_analysis: dict,llm_model: str) -> str:
    """
    当 LLM 判断为实现性错误时，使用 LLM 分析具体的实现问题并提供修复建议。
    返回一个包含分析和建议的字符串。
    """
    logging.info("🤖 LLM: 正在分析实现性错误并提供修复建议...")
    base_prompt = f"""
[SYSTEM]
你是一位顶级的竞赛编程导师。学生的代码因实现性错误而被判错误，但其核心逻辑是健全的。
你的任务是精确地指出代码中存在错误的具体实现细节，并提供清晰、可操作的修复建议。

[问题陈述]
{problem_desc}

[学生代码]
```{SUBMISSION_LANGUAGE.lower()}
{student_code}
[LLM 对实现性错误的初步分析]
原因：{error_analysis.get('reasoning', '未提供原因。')}
"""
    structured_prompt = base_prompt + """
analysis: 仔细检查学生代码，找出包含 Bug 的确切代码行或代码段，并详细解释为什么它错了。
suggestion: 提供修正后的代码片段或清晰的修复说明。如果存在多个问题，请一并说明。
"""
    natural_prompt = base_prompt + """
[任务]
请按照以下格式输出你的分析和建议，不要添加任何额外的解释性文字：
实现错误分析:
<在这里对错误的详细分析>
建议修复:
<在这里提供修正后的代码片段或具体说明>
"""

    try:
        llm = LLM(model=llm_model)
        analysis = None
        suggestion = None

        # === 主模式：尝试结构化输出 ===
        try:
            response = llm(structured_prompt, structured_output=ImplementationAnalysisOutput.model_json_schema()).result()
            structured_data = response.get("structured_output")

            if structured_data and "analysis" in structured_data and "suggestion" in structured_data:
                analysis = structured_data.get("analysis")
                suggestion = structured_data.get("suggestion")
                logging.info("✅ AI 已通过结构化输出生成分析和建议。")
        
        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 将尝试自然语言解析方式...")

        # === 备用模式：如果主模式失败，则尝试自然语言解析 ===
        if analysis is None or suggestion is None:
            response = llm(natural_prompt).result()
            content = response.get("content", "")
            logging.debug(f"AI 自然语言响应内容:\n{content}")

            analysis_match = re.search(r"实现错误分析:\s*\n?(.*?)建议修复:", content, re.DOTALL | re.IGNORECASE)
            fix_match = re.search(r"建议修复:\s*\n?(.*)", content, re.DOTALL | re.IGNORECASE)
            
            analysis = analysis_match.group(1).strip() if analysis_match else "LLM 未提供具体分析。"
            suggestion = fix_match.group(1).strip() if fix_match else "LLM 未提供具体修复建议。"

            if analysis_match and fix_match:
                logging.info("✅ AI 已按自然语言格式返回分析和建议。")

        # --- 构建并返回最终结果 ---
        result = {
            "error_type": "implementation",
            "reasoning": error_analysis.get('reasoning', '未提供原因。'),
            "implementation_analysis": analysis,
            "fix_suggestions": suggestion
        }
        
        logging.info(f"实现错误分析:\n{analysis}\n\n建议修复:\n{suggestion}")
        return result

    except Exception as e:
        logging.error(f"❌ 使用 LLM 分析实现错误时发生严重错误: {e}")
        logging.error(traceback.format_exc())
        return {
            "error_type": "implementation",
            "reasoning": error_analysis.get('reasoning', 'Analysis failed'),
            "implementation_analysis": f"LLM analysis failed: {e}",
            "fix_suggestions": "Unable to provide suggestions due to an error."
    }