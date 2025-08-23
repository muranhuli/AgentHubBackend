import uuid
import re
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
import requests
import json
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
BASE_URL = "https://oj.qd.sdu.edu.cn"
PROBLEM_CODE = "SDUOJ-1204"
JUDGETEMPLATE = {
    "C++14": 6,
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
SUBMISSION_LANGUAGE_ID = JUDGETEMPLATE.get(SUBMISSION_LANGUAGE)

def submit_solution(session: requests.Session, problem_id: str, code: str, language: str):
    """
    将生成的代码提交到 SDUOJ，并返回 submissionId。
    """
    # 提交API
    submission_url = f"{BASE_URL}/api/submit/create"
    submission_payload = {
        "problemCode": PROBLEM_CODE,
        "judgeTemplateId": SUBMISSION_LANGUAGE_ID,
        "code": code,
        "language": language
    }

    # 使用 logging.info 记录常规流程信息
    logging.info(f"正在向题目 ID '{problem_id}' 提交代码...")
    logging.info(f"  - API URL: {submission_url}")
    logging.info(f"  - Payload: {json.dumps(submission_payload, indent=2)}")  # 打印格式化的JSON载荷

    # 将网络请求和错误处理包裹在 try...except 中
    try:
        response = session.post(submission_url, json=submission_payload)

        # 记录原始响应状态，便于调试
        logging.info(f"服务器响应状态码: {response.status_code}")

        # 检查是否有HTTP错误
        response.raise_for_status()

        # 解析JSON响应
        response_data = response.json()
        logging.info(f"服务器响应内容: {json.dumps(response_data, indent=2)}")

        if response_data.get("code") == 0 and "data" in response_data:
            submission_id = response_data["data"]
            # 记录成功信息
            logging.info(f"✅ 代码提交成功！Submission ID: {submission_id}")
            return submission_id
        else:
            error_msg = response_data.get("message", "提交失败 (未知原因)")
            # 使用 logging.error 记录失败信息
            logging.error(f"❌ 提交失败: {error_msg}")
            logging.error(f"服务器返回的完整响应: {response_data}")
            return None

    except requests.exceptions.RequestException as e:
        # 使用 logging.critical 记录严重错误，如网络问题
        logging.critical(f"❌ 提交请求时发生网络错误: {e}")
        return None
    except json.JSONDecodeError as e:
        # 记录JSON解析错误
        logging.error(f"❌ 解析服务器响应失败，返回的不是有效的JSON。")
        logging.error(f"   原始响应文本: {response.text}")
        return None
    except Exception as e:
        # 捕获其他所有未知错误
        logging.critical(f"❌ 在提交过程中发生未知错误: {e}")
        # 打印完整的错误栈到日志中，便于深度调试
        logging.critical(traceback.format_exc())
        return None
