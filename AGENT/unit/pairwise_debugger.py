# AGENT/unit/pairwise_debugger.py (重构版)

import logging
import uuid
import json
from typing import List

# 导入核心框架和算子
from core.Context import get_context
from coper.Service import Service
from coper.Minio import Minio
from AGENT.unit.pydantic_models import TestCase,SolutionOutput  # 假设 pydantic 模型在同级目录下

# --- 核心修改：从其他模块导入具体的功能实现 ---
from AGENT.unit.sandbox_executor import run_code_in_sandbox
from AGENT.unit.generate_edge_cases import generate_edge_cases
# 假设 debug_and_fix 和 generate_brute_force_solution 在一个 llm_utils.py 或类似文件中
# 如果它们在各自独立的文件中，请相应修改
from AGENT.unit.debug_and_fix import debug_and_fix 
# 假设 generate_brute_force_solution 在一个单独的文件或与debug_and_fix在一起
# from AGENT.unit.llm_solvers import generate_brute_force_solution # 示例路径

# 注意：generate_brute_force_solution 在您给出的代码中仍然是本地实现的。
# 这里我暂时保留它的本地实现，但理想情况下它也应该被移出去。
from coper.LLM import LLM
from pydantic import BaseModel, Field

def generate_brute_force_solution(problem_details: dict, model_identifier: str, language: str):
    """请求LLM生成一个保证正确性但可能超时的暴力解法"""
    logging.info("⚔️ 正在生成暴力解法代码用于对拍...")
    prompt = f"""
[SYSTEM]
你是一名精通 {language} 的专家级程序员。你的任务是为下面的问题提供一个**暴力解法 (Brute-force Solution)**。
这个解法的首要目标是**绝对的正确性**，即使它的时间复杂度很高（例如，指数级），会超出时间限制也无所谓。
请不要尝试任何优化，使用最直观、最简单的方式实现。

[USER]
请为以下问题编写一个 {language} 的暴力解法。

--- 问题描述 ---
{problem_details['full_markdown_description']}
--- 问题描述结束 ---
"""
    try:
        llm = LLM(model_identifier)
        response = llm(prompt, structured_output=SolutionOutput.model_json_schema()).result()
        structured_data = response.get("structured_output")
        if structured_data and structured_data.get("code"):
            logging.info("✅ 成功生成暴力解法代码。")
            return structured_data.get("code")
        logging.error("❌ LLM未能生成有效的暴力解法代码。")
        return None
    except Exception as e:
        logging.critical(f"❌ 生成暴力解法时发生错误: {e}")
        return None
# --- 导入修改结束 ---


# --- 配置信息 ---
MAX_DEBUG_ATTEMPTS = 3
DUIPAI_COUNT = 20

# --- 辅助函数 ---
def get_manual_code_input() -> str:
    """获取用户手动输入的多行代码"""
    logging.info("请输入您修改后的完整代码。输入完成后，在新的一行输入 '_EOF_' 并按回车键结束：")
    lines = []
    while True:
        line = input()
        if line.strip() == '_EOF_':
            break
        lines.append(line)
    return "\n".join(lines)

# --- 主对拍与调试函数 ---
def pairwise_testing_mode(problem_details: dict, code_to_test: str, llm_model: str, language: str):
    """执行对拍测试，并在失败时进入调试修复循环。"""
    logging.info("=" * 50)
    logging.info("⚔️ 已达到最大尝试次数，进入对拍（Pairwise Testing）模式 ⚔️")
    logging.info("=" * 50)

    # 调用导入的函数
    brute_force_code = generate_brute_force_solution(problem_details, llm_model, language)
    if not brute_force_code:
        logging.error("无法进行对拍，因为未能生成暴力解法。")
        return

    # 调用导入的函数
    test_cases_result = generate_edge_cases(problem_details, llm_model)
    if isinstance(test_cases_result, list) and all(isinstance(tc, TestCase) for tc in test_cases_result):
        # 情况A: 成功获取了结构化的 TestCase 列表
        test_cases = test_cases_result[:DUIPAI_COUNT]
        logging.info("✅ 成功获取并使用结构化测试用例。")
        
        if not test_cases:
            logging.error("LLM 返回了一个空的测试用例列表，对拍流程无法继续。")
            return
            
    elif isinstance(test_cases_result, str):
        # 情况B: 获取到的是 Markdown 字符串
        logging.warning("⚠️ 未能获取结构化测试用例，收到的是 Markdown 报告。对拍流程将无法执行。")
        logging.info("--- LLM 生成的测试用例报告 ---")
        logging.info(test_cases_result) # 打印报告以供人工参考
        # 在这种情况下，我们无法进行自动化的对拍，所以直接终止函数
        return
        
    else:
        # 情况C: 返回了空列表或其他未知类型
        logging.error("未能生成任何测试用例，或返回了未知类型的数据。对拍流程无法继续。")
        return

    def format_cases_for_log(cases: List[TestCase]) -> str:
        output = ["🧪 LLM 动态生成的测试用例"]
        output.append("=" * 40)
        case_groups = {}
        for case in cases:
            case_groups.setdefault(case.case_type, []).append(case)
        type_names = {"basic": "📝 基础用例", "boundary": "🎯 边界用例", "edge": "⚡ 极值用例"}
        for case_type, cases_in_group in case_groups.items():
            output.append(f"\n{type_names.get(case_type, case_type)}:")
            for i, case in enumerate(cases_in_group, 1):
                input_preview = (case.input_data[:70] + '...') if len(case.input_data) > 70 else case.input_data
                output_preview = (case.expected_output[:70] + '...') if len(case.expected_output) > 70 else case.expected_output
                output.append(f"  {i}. {case.description} -> 输入: `{input_preview}`, 期望输出: `{output_preview}`")
        return "\n".join(output)

    logging.info(format_cases_for_log(test_cases))

    sandbox = Service("code-sandbox")
    ctx = get_context()
    minio_client = ctx.minio
    bucket_name = f"duipai-{str(uuid.uuid4())[:8]}"
    minio_operator = Minio()

    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
        logging.info(f"✅ 成功创建用于对拍的 Minio 存储桶: {bucket_name}")

        current_code = code_to_test
        debug_attempt = 0
        while debug_attempt < MAX_DEBUG_ATTEMPTS:
            logging.info(f"\n--- 调试修复循环: 第 {debug_attempt + 1}/{MAX_DEBUG_ATTEMPTS} 轮 ---")
            all_passed = True
            user_choice = ''

            for i, case in enumerate(test_cases):
                logging.info(f"  -> 测试用例 #{i + 1}/{len(test_cases)}: {case.description}")
                
                # 调用导入的函数
                std_output = run_code_in_sandbox(sandbox, minio_operator, brute_force_code, case.input_data, language, bucket_name)
                my_output = run_code_in_sandbox(sandbox, minio_operator, current_code, case.input_data, language, bucket_name)

                if std_output.strip() != my_output.strip():
                    all_passed = False
                    logging.error("❌ 对拍发现错误！")
                    logging.error(f"  - 输入:\n{case.input_data}")
                    logging.error(f"  - 标准输出 (Expected):\n{std_output}")
                    logging.error(f"  - 你的输出 (Got):\n{my_output}")

                    user_choice = input("\n请选择操作：[1] 让AI自动修复 [2] 为AI提供提示后修复 [3] 手动修改代码 [4] 放弃调试\n> ").strip()

                    if user_choice == '1':
                        # 调用导入的函数
                        current_code = debug_and_fix(problem_details, current_code, case.input_data, std_output, my_output, language, llm_model)
                    elif user_choice == '2':
                        hint = input("请输入你的提示信息：\n> ")
                        # 调用导入的函数
                        current_code = debug_and_fix(problem_details, current_code, case.input_data, std_output, my_output, language, llm_model, user_hint=hint)
                    elif user_choice == '3':
                        current_code = get_manual_code_input()
                    else:
                        logging.info("用户选择放弃调试。")
                        return # 直接返回，finally块会执行
                    break

            if all_passed:
                logging.info("🎉🎉🎉 恭喜！代码已通过所有对拍测试用例！")
                break
            
            if user_choice == '4':
                break

            debug_attempt += 1

        if not all_passed:
            logging.error(f"达到最大调试次数 ({MAX_DEBUG_ATTEMPTS})，仍未修复所有问题。")

    finally:
        try:
            logging.info(f"正在清理并删除 Minio 存储桶: {bucket_name}...")
            if minio_client.bucket_exists(bucket_name):
                objects = minio_client.list_objects(bucket_name, recursive=True)
                object_names = [obj.object_name for obj in objects]
                if object_names:
                    errors = minio_client.remove_objects(bucket_name, object_names)
                    for error in errors:
                        logging.warning(f"删除 Minio 对象时出错: {error}")
                minio_client.remove_bucket(bucket_name)
                logging.info(f"✅ 成功清理 Minio 存储桶。")
        except Exception as e:
            logging.error(f"❌ 清理 Minio 存储桶时发生严重错误: {e}")