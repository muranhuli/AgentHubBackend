# # import uuid
# # import re
# # from coper.LLM import LLM
# # from coper.basic_ops import Mul
# # from core.Context import Context
# # from coper.Service import Service
# # import logging
# # log_filename = f"judge_error_type.log"
# # logging.basicConfig(
# #     level=logging.INFO,
# #     format='%(asctime)s [%(levelname)s] - %(message)s',
# #     handlers=[
# #         logging.FileHandler(log_filename, encoding='utf-8'),
# #         logging.StreamHandler()  # 同时输出到控制台
# #     ]
# # )
# # SUBMISSION_LANGUAGE = "C++14"
# # def debug_and_fix(problem_details: dict, buggy_code: str, failed_case_input: str, expected_output: str,
# #                            actual_output: str, language: str, model: str, user_hint: str = None):
# #     """请求LLM分析并修复bug"""
# #     logging.info("🤖 正在请求 AI 分析并修复代码...")

# #     prompt = f"""
# # [SYSTEM]
# # 你是一位顶级的软件调试专家，精通 {language} 语言。你的任务是分析一段有错误的代码，并根据一个导致失败的测试用例来修复它。

# # [USER]
# # 请分析以下有问题的代码。它在处理给定的输入时，未能产生预期的输出。

# # --- 问题描述 ---
# # {problem_details['full_markdown_description']}
# # --- 问题描述结束 ---

# # --- 失败的测试用例 ---
# # 输入 (Input):
# # {failed_case_input}
# # 预期的输出 (Expected Output):
# # {expected_output}
# # 实际的错误输出 (Actual Output):
# # {actual_output}
# # --- 失败的测试用例结束 ---
# # """
# #     if user_hint:
# #         prompt += f"""
# # --- 人类开发者的提示 ---
# # {user_hint}
# # --- 提示结束 ---
# # """
# #     prompt += f"""
# # --- 有问题的代码 ---
# # ```{language.lower()}
# # {buggy_code}
# # --- 有问题的代码结束 ---
# # 请在'thought'部分详细分析错误的原因，然后在'code'部分提供完整的、修正后的代码。
# # """
# #     try:
# #         llm = LLM(model)
# #         response = llm(prompt, structured_output=SolutionOutput.model_json_schema()).result()
# #         structured_data = response.get("structured_output")
# #         if structured_data and structured_data.get("code"):
# #             logging.info("✅ AI 已生成修正后的代码。")
# #             return structured_data.get("code")
# #         logging.error("❌ AI 未能生成有效的修正代码。将返回原始代码。")
# #         return buggy_code
# #     except Exception as e:
# #         logging.critical(f"❌ 请求 AI 修复代码时发生错误: {e}")
# #         return buggy_code
# import uuid
# import re
# import logging
# import traceback
# import json
# from coper.LLM import LLM
# from coper.basic_ops import Mul
# from core.Context import Context
# from coper.Service import Service

# log_filename = f"judge_error_type.log"
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] - %(message)s',
#     handlers=[
#         logging.FileHandler(log_filename, encoding='utf-8'),
#         logging.StreamHandler()  # 同时输出到控制台
#     ]
# )

# SUBMISSION_LANGUAGE = "C++14"

# def debug_and_fix(problem_details: dict, buggy_code: str, failed_case_input: str, expected_output: str,
#                   actual_output: str, language: str, model: str, user_hint: str = None):
#     """请求LLM分析并修复bug"""
#     logging.info("🤖 正在请求 AI 分析并修复代码...")

#     # 创建基础提示
#     prompt = f"""
# [SYSTEM]
# 你是一位顶级的软件调试专家，精通 {language} 语言。你的任务是分析一段有错误的代码，并根据一个导致失败的测试用例来修复它。

# [USER]
# 请分析以下有问题的代码。它在处理给定的输入时，未能产生预期的输出。

# --- 问题描述 ---
# {problem_details['full_markdown_description']}
# --- 问题描述结束 ---

# --- 失败的测试用例 ---
# 输入 (Input):
# {failed_case_input}
# 预期的输出 (Expected Output):
# {expected_output}
# 实际的错误输出 (Actual Output):
# {actual_output}
# --- 失败的测试用例结束 ---
# """
#     if user_hint:
#         prompt += f"""
# --- 人类开发者的提示 ---
# {user_hint}
# --- 提示结束 ---
# """
#     prompt += f"""
# --- 有问题的代码 ---
# {language.lower()}
# {buggy_code}
# --- 有问题的代码结束 ---
# """
    
#     # 结构化输出提示
#     structured_prompt = prompt + """
# 请在'thought'部分详细分析错误的原因，然后在'code'部分提供完整的、修正后的代码。
# """
    
#     # 自然语言提示
#     natural_prompt = prompt + """
# 请按照以下格式输出：
# 1. 首先在'分析'部分详细说明错误原因
# 2. 然后在'修复后的代码'部分提供完整的、修正后的代码
# 3. 最后在'解释'部分简要说明修复的关键点

# 请将修复后的代码放在单独的代码块中，使用以下格式：
# {language.lower()}
# // 修复后的代码
# ...

# """
    
#     try:
#         llm = LLM(model)
#         fixed_code = None
        
#         # 首先尝试结构化输出方式
#         try:
#             # 定义期望的结构化输出格式
#             structured_output_schema = {
#                 "type": "object",
#                 "properties": {
#                     "thought": {"type": "string"},
#                     "code": {"type": "string"}
#                 },
#                 "required": ["thought", "code"]
#             }
            
#             response = llm(structured_prompt, structured_output=structured_output_schema).result()
#             structured_data = response.get("structured_output")
            
#             if structured_data and structured_data.get("code"):
#                 fixed_code = structured_data.get("code")
#                 logging.info("✅ AI 已通过结构化输出生成修正后的代码。")
        
#         except Exception as e:
#             logging.warning(f"结构化输出失败: {e}, 尝试自然语言方式...")
        
#         # 如果结构化输出失败，尝试自然语言方式
#         if not fixed_code:
#             response = llm(natural_prompt).result()
#             content = response.get("content", "")
            
#             logging.debug(f"AI 响应内容:\n{content}")
            
#             # 尝试从响应中提取修复后的代码
#             code_match = re.search(rf"`{language.lower()}\s*(.*?)\s*`", content, re.DOTALL)
#             if code_match:
#                 fixed_code = code_match.group(1).strip()
#                 logging.info("✅ AI 已通过自然语言生成修正后的代码。")
#             else:
#                 # 如果找不到代码块，尝试查找其他格式的代码
#                 logging.warning("❌ 未找到格式化的代码块，尝试提取代码片段...")
#                 code_match = re.search(r"修复后的代码[:：]?\s(.?)(?=解释|$)", content, re.DOTALL)
#                 if code_match:
#                     fixed_code = code_match.group(1).strip()
#                     logging.info("✅ AI 已生成修正后的代码（非格式化）。")
        
#         # 如果两种方式都失败，返回原始代码
#         if not fixed_code:
#             logging.error("❌ AI 未能生成有效的修正代码。将返回原始代码。")
#             return buggy_code
        
#         return fixed_code
        
#     except Exception as e:
#         logging.critical(f"❌ 请求 AI 修复代码时发生错误: {e}")
#         logging.error(traceback.format_exc())
#         return buggy_code


import re
import logging
import traceback
import json
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
from AGENT.unit.pydantic_models import SolutionOutput

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

def debug_and_fix(problem_details: dict, buggy_code: str, failed_case_input: str, expected_output: str,
                  actual_output: str, language: str, model: str, user_hint: str = None):
    """请求LLM分析并修复bug"""
    logging.info("🤖 正在请求 AI 分析并修复代码...")

    # 创建基础提示
    prompt = f"""
[SYSTEM]
你是一位顶级的软件调试专家，精通 {language} 语言。你的任务是分析一段有错误的代码，并根据一个导致失败的测试用例来修复它。

[USER]
请分析以下有问题的代码。它在处理给定的输入时，未能产生预期的输出。

--- 问题描述 ---
{problem_details['full_markdown_description']}
--- 问题描述结束 ---

--- 失败的测试用例 ---
输入 (Input):
{failed_case_input}
预期的输出 (Expected Output):
{expected_output}
实际的错误输出 (Actual Output):
{actual_output}
--- 失败的测试用例结束 ---
"""
    if user_hint:
        prompt += f"""
--- 人类开发者的提示 -f--
{user_hint}
--- 提示结束 ---
"""
    prompt += f"""
--- 有问题的代码 ---
{language.lower()}
{buggy_code}
--- 有问题的代码结束 ---
"""
    
    # 结构化输出提示
    structured_prompt = prompt + """
请严格遵循给定的结构
"""
    
    # 自然语言提示
    natural_prompt = prompt + f"""
【输出格式要求】
1. 先写一段简短的分析，放在标签 <analysis> 和 </analysis> 之间。
2. 紧接着给出 **完整** 的修复后代码，放在一对 ```{language.lower()} 和 ``` 之间，中间不要插入任何解释文字。
3. 最后如有需要，再用 <note> 和 </note> 写一段简短说明。

示例模板：
<analysis>
这里写错误原因分析
</analysis>

```{language.lower()}
// 修复后的完整代码
...
<note>
（可选）修复关键点
</note>
【重要】务必保持上述格式，否则解析会失败。
"""
    
    try:
        llm = LLM(model)
        fixed_code = None
        
        # 首先尝试结构化输出方式
        try:          
            response = llm(structured_prompt, structured_output=SolutionOutput.model_json_schema()).result()
            structured_data = response.get("structured_output")
            
            if structured_data and structured_data.get("code"):
                fixed_code = structured_data.get("code")
                logging.info("✅ AI 已通过结构化输出生成修正后的代码。")
        
        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 尝试自然语言方式...")
        
        # 如果结构化输出失败，尝试自然语言方式
        if not fixed_code:
            response = llm(natural_prompt).result()
            content = response.get("content", "")
            logging.debug(f"AI 响应内容:\n{content}")

            # 统一提取 ```cpp ... ``` 或 ``` ... ```
            pattern = rf"```{re.escape(language.lower())}(?:\s*\n)?(.*?)```"
            m = re.search(pattern, content, re.DOTALL)
            if not m:                      # 再试一次不带语言标记
                m = re.search(r"```(?:.*?\n)?(.*?)```", content, re.DOTALL)

            if m:
                fixed_code = m.group(1).strip()
                logging.info("✅ AI 已按自然语言格式返回代码。")
        
        # 如果两种方式都失败，返回原始代码
        if not fixed_code:
            logging.error("❌ AI 未能生成有效的修正代码。将返回原始代码。")
            return buggy_code
        
        return fixed_code
        
    except Exception as e:
        logging.critical(f"❌ 请求 AI 修复代码时发生错误: {e}")
        logging.error(traceback.format_exc())
        return buggy_code


