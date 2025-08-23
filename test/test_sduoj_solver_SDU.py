import requests
import json
import os
import getpass
import traceback
import time
import logging  # 1. 导入 logging 模块
from bs4 import BeautifulSoup

# 导入已有的 coper 模块
from coper.LLM import LLM
from core.Context import Context


# --- 1. 配置信息 ---
BASE_URL = "https://oj.qd.sdu.edu.cn"
PROBLEM_CODE = "SDUOJ-1155" 
LLM_MODEL_NAME = "DeepSeek-R1"
LLM_PROVIDER = "SDU"
LOG_FILE = "llm_output.log" # 定义日志文件名
LLM_LOGGER_NAME = "llm_response_logger" # 定义 logger 名称

JUDGETEMPLATE = {
    "C++14" : 6,
    "Python3.6": 13,
    "Java8": 14,
    "C11": 19,
    "C++17": 32,
    "Java17": 37,
    "Python3.11": 38,
    "PyPy3.10": 42,
    "C++20": 50,
    "Java21": 51,
    "Python3.12": 52,
    "Rust 1.78.0": 53
}
SUBMISSION_LANGUAGE = "C++14"
SUBMISSION_LANGUAGE_ID=JUDGETEMPLATE.get(SUBMISSION_LANGUAGE)

# --- 2. 日志设置函数 ---
def setup_logging():
    """配置一个专用于记录LLM完整响应的logger。"""
    logger = logging.getLogger(LLM_LOGGER_NAME)
    logger.setLevel(logging.INFO) # 设置记录级别为INFO
    
    # 防止日志消息向上传递到根logger
    logger.propagate = False
    
    # 如果logger已经有handler，则不再添加，防止重复记录
    if logger.hasHandlers():
        return

    # 创建一个文件处理器，以追加模式('a')写入日志文件
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    
    # 创建一个格式化器，定义日志消息的格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s\n%(message)s\n')
    file_handler.setFormatter(formatter)
    
    # 将处理器添加到logger
    logger.addHandler(file_handler)
    
    print(f"📝 LLM 的完整响应将被记录到文件: '{LOG_FILE}'")


# --- 3. 核心功能函数 ---

def login(session: requests.Session, username: str, password: str):
    """登录到 SDUOJ"""
    login_url = f"{BASE_URL}/api/user/login"
    login_payload = {"username": username, "password": password}
    print("正在尝试登录...")
    response = session.post(login_url, json=login_payload)
    response.raise_for_status()
    response_data = response.json()
    if response_data.get("code") == 0:
        print(f"✅ 登录成功！欢迎, {username}!")
        return True
    else:
        error_msg = response_data.get("message", "未知登录错误")
        print(f"❌ 登录失败: {error_msg}")
        return False

def get_problem_details(session: requests.Session, problem_code: str):
    """
    最终策略: 直接调用API，并从返回的单一Markdown字段中提取全部题目信息。
    """
    problem_api_url = f"{BASE_URL}/api/problem/query"
    params = {"problemCode": problem_code}
    
    print(f"正在通过API获取题目 '{problem_code}' 的详细信息...")
    response = session.get(problem_api_url, params=params)
    response.raise_for_status()
    response_data = response.json()
        
    if response_data.get("code") == 0 and "data" in response_data:
        problem_data = response_data["data"]
            
        desc_dto = problem_data.get("problemDescriptionDTO", {})
        markdown_content = desc_dto.get("markdownDescription")

        if not markdown_content:
            print("❌ API响应中缺少 'markdownDescription' 内容。")
            return None

        details = {
            "id": problem_data.get("problemId"),
            "title": problem_data.get("problemTitle"),
            "full_markdown_description": markdown_content 
        }

        print("✅ 题目信息获取成功！")
        return details
    else:
        error_msg = response_data.get("message", "获取题目信息失败")
        print(f"❌ API请求失败: {error_msg}")
        return None



def generate_solution_with_llm(problem_details: dict, model_name: str, provider: str):
    """构建 prompt 并调用 SDU 大模型生成解决方案代码。"""
    print(f"🤖 正在调用大模型 ({provider}/{model_name}) 生成解决方案...")
    prompt = f"""
[SYSTEM]
You are a world-class competitive programming expert, specializing in {SUBMISSION_LANGUAGE}. Your sole purpose is to write a complete, correct, and runnable C++ program to solve the given problem. You must follow all instructions precisely. For standard I/O, use `<iostream>` and `cin`, `cout`.

[USER]
Solve the following programming problem using {SUBMISSION_LANGUAGE}:

--- START OF PROBLEM DESCRIPTION (MARKDOWN) ---

{problem_details['full_markdown_description']}

--- END OF PROBLEM DESCRIPTION ---

**INSTRUCTION:**
Write the full C++ code solution now. Your response must contain ONLY the C++ code inside a single markdown block (using ```cpp), and nothing else. 不要输出你的思考过程
"""
    
    llm = LLM(model_name, provider) 
    response_dict = llm(prompt).result()
    
    # 4. 获取 logger 实例并记录响应
    llm_logger = logging.getLogger(LLM_LOGGER_NAME)
    
    # --- 全新且正确的日志记录逻辑 ---
    if isinstance(response_dict, dict):
        # 从返回的字典中分别获取 content 和 reasoning_content
        code_content = response_dict.get("content", "")
        reasoning_content = response_dict.get("reasoning_content", "")
        
        # 将两者都记录到日志中
        log_message = (
            f"--- [LLM Response] Problem: {problem_details.get('title', 'N/A')} ({PROBLEM_CODE}) ---\n"
            f"--- Reasoning ---\n"
            f"{reasoning_content}\n"
            f"--- Code Content ---\n"
            f"{code_content}\n"
            f"--- [End of Response] ---"
        )
        llm_logger.info(log_message)

    else:
        error_message = f"LLM未能返回有效的字典内容。收到的响应: {response_dict}"
        print(f"❌ {error_message}")
        llm_logger.error(f"--- [LLM Call Failed] ---\n{error_message}\n--- [End of Error] ---")
        return None

    # --- 代码提取逻辑现在只关注 code_content ---
    content_for_extraction = code_content if code_content else ""

    if '```cpp' in content_for_extraction:
        code = content_for_extraction.split('```cpp', 1)[1].rsplit('```', 1)[0].strip()
    elif '```' in content_for_extraction:
        code = content_for_extraction.split('```', 1)[1].rsplit('```', 1)[0].strip()
    else:
        # 如果代码内容为空，或者包含问候语，则认为失败
        if not content_for_extraction or any(word in content_for_extraction for word in ["你好", "您好", "帮助", "Hello", "help"]):
            print("❌ LLM返回了非代码内容或代码内容为空。")
            print(f"LLM 原始响应 (已记录到日志)")
            return None
        code = content_for_extraction.strip()
           
    # 如果成功提取出代码，才打印
    if code:
        print("✅ 大模型已生成代码:")
        print("-" * 30); print(code); print("-" * 30)
        return code
    else:
        print("❌ 未能从LLM响应中提取出有效的代码。")
        return None
        

def submit_solution(session: requests.Session, problem_id: str, problem_code: str, code: str, language: str):
    """
    将生成的代码提交到 SDUOJ，并返回 submissionId。
    """
    submission_url = f"{BASE_URL}/api/submit/create"
    submission_payload = {
        "problemCode": PROBLEM_CODE, 
        "judgeTemplateId": SUBMISSION_LANGUAGE_ID, 
        "code": code,
        "language": language
    }
    
    print(f"正在向题目 ID '{problem_id}' 提交代码...")
    response = session.post(submission_url, json=submission_payload)
    response.raise_for_status()
    response_data = response.json()
        
    if response_data.get("code") == 0 and "data" in response_data:
        submission_id = response_data["data"]
        print(f"✅ 代码提交成功！Submission ID: {submission_id}")
        return submission_id
    else:
        error_msg = response_data.get("message", "提交失败")
        print(f"❌ 提交失败: {error_msg}")
        print(f"服务器响应: {response_data}")
        return None

def check_submission_status(session: requests.Session, submission_id: str):
    """
    轮询检查提交状态，直到评测完成。
    """
    status_url = f"{BASE_URL}/api/submit/query"
    params = {"submissionId": submission_id}
    
    print("开始查询评测结果...")

    judge_status = {
        -4: "Queueing", -3: "Compiling", -2: "Judging",
        -1: "End (Internal System Status)", 0: "Pending", 1: "Accepted",
        2: "Time Limit Exceeded", 3: "Memory Limit Exceeded", 4: "Runtime Error",
        5: "System Error", 6: "Wrong Answer", 7: "Presentation Error",
        8: "Compilation Error", 9: "Output Limit Exceeded", 99: "Cancelled"
    }
    finished_statuses = {1, 2, 3, 4, 5, 6, 7, 8, 9, 99, -1}
    max_wait_time = 120
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        response = session.get(status_url, params=params)
        response.raise_for_status()
        response_data = response.json()
            
        if response_data.get("code") == 0 and "data" in response_data:
            result_data = response_data["data"]
            status_code = result_data.get("judgeResult")
            status_text = judge_status.get(status_code, f"Unknown Status ({status_code})") if status_code is not None else "Waiting for Judge"
                
            print(f"  当前状态: {status_text}...")

            if status_code in finished_statuses:
                print("-" * 50)
                print("🎉 评测完成！最终结果:")
                print(f"  - 结果: {status_text}")
                if status_code == 1:
                    print(f"  - 耗时: {result_data.get('usedTime')} ms")
                    print(f"  - 内存: {result_data.get('usedMemory')} KB")
                if status_code == 8 and result_data.get("judgeInfo"):
                    print("编译错误信息:")
                    print(result_data.get("judgeInfo"))
                print("-" * 50)
                return result_data
        else:
            print("  查询失败或数据格式不符，稍后重试...")

        time.sleep(2)

    print("❌ 查询超时，评测可能仍在进行中或已失败。")
    return None

# --- 主执行流程 __main__ ---
def main():
    """主执行函数，封装所有流程"""
    # 5. 在主函数开头调用日志设置函数
    setup_logging()

    username = os.getenv("SDUOJ_USERNAME", "202300130111")
    password = os.getenv("SDUOJ_PASSWORD", "1517287203Syx")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'{BASE_URL}/v2/problem/{PROBLEM_CODE}',
    })

    print("-" * 50)
    print(f"准备开始自动化流程，目标题目: {PROBLEM_CODE}")
    print("-" * 50)

    with Context(task_id="sduoj-solver-sdu-llm"):
        if not login(session, username, password): return
            
        problem_details = get_problem_details(session, PROBLEM_CODE)
        if not problem_details: return
                
        solution_code = generate_solution_with_llm(problem_details, LLM_MODEL_NAME, LLM_PROVIDER)
            
        if not solution_code: return
                
        problem_id_for_submission = problem_details.get("id")
        if not problem_id_for_submission:
            print("❌ 未能从题目详情中获取用于提交的 problemId。")
            return

        print(f"\n即将把生成的代码提交到题目: {PROBLEM_CODE} ({problem_details.get('title', '')})")
            
        confirm = input("确认提交吗? (y/n): ").lower()
        if confirm == 'y':
            submission_id = submit_solution(
                session, 
                str(problem_id_for_submission),
                PROBLEM_CODE, 
                solution_code, 
                SUBMISSION_LANGUAGE
            )
            if submission_id:
                check_submission_status(session, submission_id)
        else:
            print("操作已取消，未提交代码。")


if __name__ == "__main__":
    start_time=time.time()
    main()
    end_time=time.time()
    print(f"\n总耗时：{end_time-start_time}")