import uuid
import re
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
import requests
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

def login(session: requests.Session, username: str, password: str) -> bool:
    login_url = f"{BASE_URL}/api/user/login"
    login_payload = {"username": username, "password": password}
    print("正在尝试登录...")
    r = session.post(login_url, json=login_payload, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("code") == 0:
        print(f"✅ 登录成功！欢迎, {username}!")
        return True
    else:
        print(f"❌ 登录失败: {data.get('message', '未知错误')}")
        return False
