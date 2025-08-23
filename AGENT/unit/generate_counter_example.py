import uuid
import re
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
from AGENT.unit.pydantic_models import CounterExampleOutput
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
def generate_counter_example(problem_desc: str, student_code: str, error_analysis: dict, llm_model: str) -> str:
    """
    当 LLM 判断为概念性错误时，使用 LLM 生成一个能暴露此概念性错误的测试用例（反例）。
    返回一个包含输入和正确输出的字符串。
    """
    logging.info("🤖 LLM: 正在为概念性错误生成反例...")
    
    # 构建给 LLM 的 Prompt，强调任务和上下文
    base_prompt = f"""
[SYSTEM]
你是一位顶级的竞赛编程导师。学生的代码因核心逻辑存在概念性缺陷而被判错误。
你的任务是提供一个具体的输入，用以展示这个逻辑缺陷，并给出该输入的正确输出。

[问题陈述]
{problem_desc}

[学生代码]
```{SUBMISSION_LANGUAGE.lower()}
{student_code}
[LLM 对概念性错误的分析]
LLM 先前已将错误类型判断为概念性，原因为：
{error_analysis.get('reasoning', '未提供原因。')}
[任务]
基于问题陈述和已识别出的概念性错误，设计一个特定的输入测试用例，并确定该输入对应的正确输出。
"""
    structured_prompt = base_prompt + """
    [输出要求]
你的输出必须是一个只包含 input_data 和 expected_output 键的 JSON 对象。
"""
    natural_prompt = base_prompt + """
    [输出格式]
请严格按照以下格式输出，不要添加任何额外文字：
输入:
<你生成的输入>
正确输出:
<你生成的输入对应的正确输出>
"""
    try:
        llm = LLM(model=llm_model)
        generated_input = None
        correct_output = None

        # === 主模式：尝试结构化输出 ===
        try:
            response = llm(structured_prompt, structured_output=CounterExampleOutput.model_json_schema()).result()
            structured_data = response.get("structured_output")

            if structured_data and "input_data" in structured_data and "expected_output" in structured_data:
                generated_input = structured_data.get("input_data")
                correct_output = structured_data.get("expected_output")
                logging.info("✅ AI 已通过结构化输出生成反例。")

        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 将尝试自然语言解析方式...")

        # === 备用模式：如果主模式失败，则尝试自然语言解析 ===
        if generated_input is None or correct_output is None:
            response = llm(natural_prompt).result()
            content = response.get("content", "")
            logging.debug(f"AI 自然语言响应内容:\n{content}")

            input_match = re.search(r"输入:\s*\n?(.*?)正确输出:", content, re.DOTALL | re.IGNORECASE)
            output_match = re.search(r"正确输出:\s*\n?(.*)", content, re.DOTALL | re.IGNORECASE)
            
            if input_match and output_match:
                generated_input = input_match.group(1).strip()
                correct_output = output_match.group(1).strip()
                logging.info("✅ AI 已通过自然语言解析生成反例。")
        
        # --- 构建并返回最终结果 ---
        if generated_input and correct_output:
            counter_example_info = f"LLM 生成的反例:\n输入:\n{generated_input}\n\n正确输出:\n{correct_output}\n"
            logging.info(counter_example_info)
            return counter_example_info
        else:
            logging.error("❌ 两种方式均未能成功生成反例。")
            return "LLM未能成功生成反例。"

    except Exception as e:
        logging.error(f"❌ 使用 LLM 生成反例时发生严重错误: {e}")
        logging.error(traceback.format_exc())
        return f"LLM 在生成反例时出错: {e}"