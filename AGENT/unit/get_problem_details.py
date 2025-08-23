# sduoj_problem.py
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
BASE_URL = "https://oj.qd.sdu.edu.cn"   # 按需修改

def get_problem_details(session: requests.Session, problem_code: str):
    """
    通过 SDUOJ API 获取题目详情（包含描述和可用语言模板）。
    返回 dict 或 None。
    """
    url = f"{BASE_URL}/api/problem/query"
    params = {"problemCode": problem_code}

    logging.info(f"Fetching problem details for {problem_code}")

    try:
        r = session.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logging.error(f"获取题目信息失败: {e}")
        return None

    if data.get("code") != 0 or "data" not in data:
        logging.error(f"API 返回错误: {data}")
        return None

    p = data["data"]
    desc_dto = p.get("problemDescriptionDTO", {})
    markdown = desc_dto.get("markdownDescription")
    if not markdown:
        logging.error("缺少 markdownDescription")
        return None

    return {
        "id": p.get("problemId"),
        "title": p.get("problemTitle"),
        "full_markdown_description": markdown,
        "judge_templates": p.get("judgeTemplates", [])
    }