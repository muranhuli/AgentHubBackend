# 中间值输出、手动调试、测试
import requests
import json
import os
import getpass
import traceback
import time
import logging
import re
import uuid
import tempfile
import shutil
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import List

# 导入已有的 coper 模块
from core.Context import Context
from coper.LLM import LLM
from coper.Service import Service
from coper.Minio import Minio
from core.Utils import zip_directory_to_bytes, unzip_bytes_to_directory
from core.Context import get_context

@dataclass
class TestCase:
    """测试用例数据结构"""
    input_data: str
    expected_output: str
    description: str
    case_type: str  # "basic", "boundary", "edge"

# --- 配置信息 ---
BASE_URL = "https://oj.qd.sdu.edu.cn"
PROBLEM_CODE = "SDUOJ-1000"
LLM_MODEL_FOR_ANALYSIS = "volcengine/doubao-seed-1-6-250615"
SUBMISSION_LANGUAGE = "C++14"
MAX_ATTEMPTS = 2  # 常规OJ提交尝试次数
MAX_DEBUG_ATTEMPTS = 3  # 对拍模式下的最大调试修复次数
DUIPAI_COUNT = 20  # 对拍测试用例数量
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
LANGUAGE_TO_SANDBOX_TEMPLATE = {
    "C++14": "gcc-13.3-cpp-std_14-O2",
    "C++17": "gcc-13.3-cpp-std_17-O2",
    "C++20": "gcc-13.3-cpp-std_20-O2",
    "Python3.11": "python-3.11",
    "Python3.12": "python-3.12",
}
SUBMISSION_LANGUAGE_ID = JUDGETEMPLATE.get(SUBMISSION_LANGUAGE)
MAX_PROMPT_TOKENS = 8000  # 单次询问的Prompt Token上限
TOTAL_TOKEN_LIMIT = 50000  # 整个解题过程的总Token消耗上限
JUDGE_STATUS = {
    -4: "Queueing(排队中)",
    -3: "Compiling(编译中)",
    -2: "Judging(评测中)",
    -1: "End (Internal System Status, may indicate completion)(结束)",
    0: "Pending(等待评测)",
    1: "Accepted(通过)",
    2: "Time Limit Exceeded(时间超限)",
    3: "Memory Limit Exceeded(内存超限)",
    4: "Runtime Error(运行错误)",
    5: "System Error(系统错误)",
    6: "Wrong Answer(答案错误)",
    7: "Presentation Error(格式错误)",
    8: "Compilation Error(编译错误)",
    9: "Output Limit Exceeded(输出超限)",
    99: "Cancelled(已取消)"
}
# 定义存放所有解决方案的目录名
SOLUTIONS_DIR = "solutions"
# --- 日志记录配置 ---
log_filename = f"sduoj_solver_doubao_run_{PROBLEM_CODE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)


class SolutionOutput(BaseModel):
    thought: str = Field(..., description="一步步解释代码背后逻辑的思考过程。")
    code: str = Field(..., description="用于解决问题的完整、可运行的源代码。")


# --- 核心功能函数 ---
def login(session: requests.Session, username: str, password: str):
    """登录到 SDUOJ"""
    login_url = f"{BASE_URL}/api/user/login"
    login_payload = {"username": username, "password": password}
    print("正在尝试登录...")
    response = session.post(login_url, json=login_payload)
    response.raise_for_status()  # 请求失败会直接抛出异常
    response_data = response.json()
    if response_data.get("code") == 0:
        print(f"✅ 登录成功！欢迎, {username}!")
        return True
    else:
        error_msg = response_data.get("message", "未知登录错误")
        print(f"❌ 登录失败: {error_msg}")
        return False


def get_problem_details(session: requests.Session, problem_code: str):
    """通过API获取题目详情，并包含可用的语言模板。"""
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

        judge_templates = problem_data.get("judgeTemplates", [])

        details = {
            "id": problem_data.get("problemId"),
            "title": problem_data.get("problemTitle"),
            "full_markdown_description": markdown_content,
            "judge_templates": judge_templates
        }
        print("✅ 题目信息获取成功！")
        return details
    else:
        error_msg = response_data.get("message", "获取题目信息失败")
        print(f"❌ API请求失败: {error_msg}")
        return None


def estimate_tokens(text: str) -> int:
    """
    估算包含中英文混合文本的Token数量。
    估算规则：1个汉字约2个Token，1个英文单词约1.33个Token。
    """
    if not text:
        return 0

    # 使用正则表达式分别匹配中文字符和英文单词
    # \u4e00-\u9fa5 匹配所有中文字符
    chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
    # \b\w+\b 匹配所有独立的英文单词
    english_words = re.findall(r'\b[a-zA-Z]+\b', text)

    # 计算Token数
    chinese_tokens = len(chinese_chars) * 2
    english_tokens = int(len(english_words) * 1.33)

    # 其他所有字符（数字、符号、代码）可以大致按 4个字符=1个Token 估算
    other_chars = len(text) - len(chinese_chars) - len("".join(english_words))
    other_tokens = other_chars // 4

    total_estimated_tokens = chinese_tokens + english_tokens + other_tokens
    return total_estimated_tokens


def generate_plan_with_llm(problem_details: dict, model_identifier: str, language: str) -> tuple[str | None, int]:
    """
    第一步：调用LLM，只生成解题计划，不生成代码。
    """
    logging.info("🧠 步骤 1/2: 调用大模型生成解题计划...")

    # 某些问题的限定时间可能不是1000ms

    prompt = f"""
[SYSTEM]
你是一位世界级的{language}语言算法设计师和竞赛编程教练。你的任务是仔细分析下面的编程问题，并为它设计一个清晰、分步的解题计划。

[USER]
请分析以下问题，并提供一份详细的解决方案计划。计划应包括：
1.  **核心思想**: 简要总结将要使用的主要算法或数据结构，可以从以下方案中选择：

基础算法：枚举、模拟、递归&分治、贪心、排序（选择排序、冒泡排序、插入排序、计数排序、基数排序、快速排序、归并排序、堆排序、桶排序、希尔排序、锦标赛排序、Tim排序）、前缀和&差分、二分、倍增、构造；
搜索算法：DFS、BFS、双向搜索、启发式搜索、A*、迭代加深搜索、IDA*、回溯法、Dancing Licks、Alpha-Beta剪枝、搜索优化
动态规划算法：背包DP、区间DP、DAG上的DP、树形DP、状压DP、数位DP、插头DP、计数DP、动态DP、概率DP、DP套DP、DP优化（单调队列、单调栈优化、，斜率优化、四边形不等式优化、Slope Trick优化、WQS二分、状态设计优化）
字符串算法：字符串匹配、字符串哈希、字典树、前缀算法、KMP算法、Boyer-Moore算法、Z函数、AC自动机、后缀数组、后缀自动机、后缀平衡树、广义后缀平衡树、后缀树、Manacher、回文树、序列自动机、最小表示法、Lyndon分解、Main-Lorentz算法
数学：进位制、位运算、二进制集合操作、平衡三进制、高精度计算、快速幂、置换和排列、互弧度制与坐标系、复数、数论（素数、最大公约数、数论分块、欧拉函数、筛法、Meissel-Lehmer算法、分解质因数、贝祖定理、类欧几里得算法、欧拉算法&费马小定理、乘法逆元、线性同余方程、中国剩余定理、升幂引理、阶乘取模、卢卡斯定理、同余方程、二次剩余、原根、离散对数、剩余、莫比乌斯反演、杜数筛、Powerful Number筛、Min_25筛、洲阁筛、连分数、Stern-Brocot树与Farey序列、二次城、Pell方程）、多项式与生成函数（代数基本定理、快速傅里叶变换、快速数论变换、快速沃尔什变换、Chirp Z变换、多项式牛顿迭代、多项式多点求值|快速插值、多项式初等函数、常系数齐次线性递推、多项式平移|连续点值平移、符号化方法、Lagrange反演、形似幂级数复合|复合逆、普通生成函数、指数生成函数、狄利克雷生成函数）、组合数学（排列组合、抽屉原理、容斥原理、斐波那契数列、错位排列、卡特兰数、斯特林数、贝尔数、伯努利数、Entringer Number、Eulerian Number、分拆数、范德蒙德卷积、Polya计数、图论计数）、线性代数（向量、内积和外积、矩阵、初等变换、行列式、线性空间、线性基、线性映射、特征多项式、对角化、Jordan标准型）、线性规划（单纯形法）、抽象代数（群论、环论、域论、Schreier-Sims算法）、概率论（条件概率与独立性、随机变量、随机变量的数字特征、概率不等式）、博弈论（公平组合游戏、非公平组合游戏）、数值算法（插值、数值积分、高斯消元、牛顿迭代法）、序理论、杨氏矩阵、拟阵、Beriekamp-Massey算法；
数据结构：栈、队列、链表、哈希表、并查集、堆（二叉堆、配对堆、左偏树）、块状数据结构（块状数组、块状链表、树分块、Sqrt Tree）、单调栈、单调队列、ST表、树状数组、线段树（线段树合并&分裂、李超线段树、猫树、区间最值操作&区间历史最值、划分树）、二叉搜索树&平衡树（Treap、Splay树、WBLT、替罪羊树、笛卡尔树、Size Balanced Tree、AVL树、红黑树、左偏红黑树、AA树）、跳表、可持久化数据结构（可持久化线段树、可持久化块状数组、可持久化平衡树、可持久化字典树、可持久化可并堆）、树套树（线段树套线段树、平衡树套线段树、线段树套平衡树、树状数组套权值平衡树、分块套树状数组）、K-D Tree、动态树（Link cut Tree全局平衡二叉树、Euler Tour Tree、Top Tree）、析和树、PQ树、手指树、霍夫曼树；
图论：图的存储、DFS、BFS、树上问题（树的直径、树的中心、最近公共祖先、树链剖分、树上启发式合并、虚树、树分治、动态树分治、AHU算法、树哈希、树上随机游走）、有向无环图、拓扑排序、最短路问题（最短路、差分约束、k短路、同余最短路）、生成树问题（最小生成树、最小树形图、最小直径生成树）、斯坦纳树、拆点、连通性相关（强联通分量、双联通分量、割点和桥、圆方图、点/边连通度）环计数问题、最小环、2-SAT、欧拉图、哈密顿图、二分图、平面图、弦图、图的着色、网络流（最大流、最小流、费用流、上下界网络流、Stoer-Wagner算法）、图的匹配（二分图最大匹配、二分图最大权匹配、一般图最大匹配、一般图最大权匹配）、Prufer序列、矩阵树定理、LGV引理、最大团搜索算法、支配树、图上随机游走；
计算几何：二维计算几何、三维计算几何、距离、Pick定理、三角剖分、凸包、扫描线、旋转卡壳、半平面交、平面最近点对、随机增量法、反演变换；
其他算法：离散化、双指针、离线算法、分数规划、随机化（随机函数、爬山算法、模拟退火）、悬线法、有限状态自动机、字节顺序、约瑟夫问题、格雷码、表达式求值、在一台机器上的规划任务、主元素问题、Garsia-Wachs算法、15-puzzie、Kahan求和、可多隶属/颜色段均摊、空间优化

2.  **详细步骤**: 用数字列表详细列出程序应该执行的确切步骤，包括输入读取、核心处理逻辑和输出打印。
3.  **数据结构**: 需要用到的具体数据结构（例如：数组、哈希表、并查集等）。
4.  **边界情况**: 需要考虑的潜在边界情况（例如：n=0、空输入、极大/极小的数字、题目约束等）。
5.  **时间限制**: 应使用尽可能高效的算法，使得程序能在1000ms内解决问题。
6.  **编译错误**: 依据{language}标准给出代码，尽量避免编译错误。

**重要提示** 
1.  请不要包含任何代码，你的输出应该只有解题计划。
2.  你的计划应该完全保证准确性，在此基础上提供尽量详细的解决办法。

--- 问题描述 ---
{problem_details['full_markdown_description']}
--- 问题描述结束 ---
"""

    try:
        llm = LLM(model_identifier)
        response = llm(prompt).result()

        content = response.get("content", "")
        usage = response.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        if total_tokens == 0 and content:
            total_tokens = estimate_tokens(prompt) + estimate_tokens(content)

        if not content:
            logging.error("❌ LLM未能生成解题计划。")
            return None, total_tokens

        logging.info("✅ 大模型已生成解题计划。")
        logging.info(f"--- Generated Plan ---\n{content}")
        return content, total_tokens

    except Exception as e:
        logging.critical(f"❌ 生成解题计划时发生错误: {e}")
        logging.critical(traceback.format_exc())
        return None, 0


def generate_solution_with_llm(problem_details: dict, plan: str, model_identifier: str, language: str,
                               submission_history: list, attempt_num: int):
    """
    第二步：根据问题详情、解题计划和历史失败尝试，【强制】LLM返回结构化的代码和思考过程。
    """
    logging.info(f"💻 步骤 2/2: 根据计划 (尝试 #{attempt_num}) 调用大模型生成代码 (结构化输出模式)...")

    # --- 1. 构建Prompt (现在更专注于内容，而非格式) ---
    prompt = f"""
[SYSTEM]
你是一名精通 {language} 的专家级程序员。你的任务是根据下面提供的解题计划来实现代码，并以结构化的方式输出你的思考过程和最终代码。

[USER]
请根据下面的问题描述和详细的解题计划，提供你的思考过程，并编写完整、可运行的 {language} 代码。

--- 问题描述 ---
{problem_details['full_markdown_description']}
--- 问题描述结束 ---

--- 解题计划 ---
{plan}
--- 解题计划结束 ---
"""

    # 反思部分
    if submission_history:
        logging.info(f"🔍 检测到 {len(submission_history)} 次历史提交失败，正在构建反思链...")
        reflection_prompt = "\n[SYSTEM]\n你之前根据计划实现的方案失败了。请分析下面的错误信息和失败的代码，然后提供一个修正后的版本。在你的“思考过程”（thought）部分，请解释是哪里出了问题，以及你是如何修正它的。然后，提供完整的、修正后的代码。\n"
        for i, attempt in enumerate(submission_history):
            reflection_prompt += f"\n--- 失败的尝试 #{i + 1} ---\n"
            reflection_prompt += f"我这次尝试的思考过程是: {attempt.get('thought', 'N/A')}\n"
            reflection_prompt += f"失败的代码:\n```{language.lower()}\n{attempt['code']}\n```\n"
            reflection_prompt += f"评测结果: **{attempt['result_text']}**\n"
            reflection_prompt += f"错误详情:\n```\n{attempt['error_info']}\n```\n"
        prompt += reflection_prompt

    try:
        if len(prompt) > MAX_PROMPT_TOKENS * 0.9:
            logging.warning("📜 Prompt过长，将移除最早的失败记录。")
            return generate_solution_with_llm(problem_details, plan, model_identifier, language, submission_history[1:],
                                              attempt_num)

        logging.info("--- 为大语言模型生成的Prompt ---\n" + prompt)

        llm = LLM(model_identifier)

        # --- 2. 使用结构化输出调用 LLM ---
        response = llm(
            prompt,
            structured_output=SolutionOutput.model_json_schema()
        ).result()

        # --- 3. 精确提取Token和内容 ---
        usage = response.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        if total_tokens == 0:
            # 估算逻辑作为备用
            content_for_estimation = json.dumps(response.get("structured_output", {}))
            total_tokens = estimate_tokens(prompt) + estimate_tokens(content_for_estimation)
            log_message = f"Token用量（估算）: 总计={total_tokens}"
        else:
            log_message = f"Token用量（来自API）: 总计={usage.get('total_tokens')}"

        logging.info(f"--- 来自LLM的完整原始响应 ---\n{json.dumps(response, indent=2, ensure_ascii=False)}")
        logging.info(log_message)

        # --- 4. 直接从结构化输出中获取数据，不再需要解析 ---
        structured_data = response.get("structured_output")
        if not isinstance(structured_data, dict):
            logging.error(f"❌ LLM未能返回有效的结构化输出。收到的响应: {structured_data}")
            return None, None, total_tokens

        thought = structured_data.get("thought", "")
        code = structured_data.get("code", "")

        if not code:
            logging.error("❌ 结构化输出中未能找到代码。")
            return None, thought, total_tokens

        logging.info("✅ 大模型已成功生成结构化的代码和思考过程。")
        logging.info(f"Thought Process: {thought}")
        print("-" * 30);
        print(code);
        print("-" * 30)

        # --- 5. 保存文件 (逻辑保持不变) ---
        os.makedirs(SOLUTIONS_DIR, exist_ok=True)
        file_name = f"{PROBLEM_CODE}_attempt_{attempt_num}.md"
        file_path = os.path.join(SOLUTIONS_DIR, file_name)
        lang_tag = "cpp" if language == "C++" else language.lower()
        file_content = f"# {PROBLEM_CODE} 的解决方案 - 尝试 #{attempt_num}\n\n"
        file_content += f"## 计划\n\n{plan}\n\n"
        if submission_history:
            file_content += "## 关于过去失败的反思\n\n此代码是基于先前错误修正后的版本。\n\n"
        file_content += f"## 思考过程\n\n{thought}\n\n"
        file_content += f"## 生成的代码 ({language})\n\n```{lang_tag}\n{code}\n```\n```\n"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        logging.info(f"💾 解决方案已成功保存到: {file_path}")

        return code, thought, total_tokens

    except Exception as e:
        logging.critical(f"❌ 调用或解析LLM时发生严重错误: {e}")
        logging.critical(traceback.format_exc())
        return None, None, 0


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


def check_submission_status(session: requests.Session, submission_id: str):
    """
    【最终修正版】轮询检查提交状态，优先处理 judgeLog，并结合 checkpointResults。
    """
    status_url = f"{BASE_URL}/api/submit/query"
    params = {"submissionId": submission_id}

    logging.info("开始查询评测结果...")
    finished_statuses = {1, 2, 3, 4, 5, 6, 7, 8, 9, 99, -1}
    max_wait_time, start_time = 120, time.time()

    while time.time() - start_time < max_wait_time:
        response = session.get(status_url, params=params)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("code") == 0 and "data" in response_data:
            result_data = response_data["data"]
            status_code = result_data.get("judgeResult")

            status_text = JUDGE_STATUS.get(status_code, f"Unknown Status ({status_code})")

            logging.info(f"  当前状态: {status_text}...")

            if status_code in finished_statuses:
                logging.info("-" * 50)
                logging.info("🎉 评测完成！最终结果:")
                logging.info(f"  - 结果: {status_text}")
                
                # --- 新的、更完善的日志提取逻辑 ---
                if status_code != 1: # 如果不是 Accepted
                    # 1. 优先处理 judgeLog
                    judge_log_raw = result_data.get("judgeLog")
                    if judge_log_raw:
                        # 清理常见的转义字符问题，例如将 '\\n' 替换为 '\n'
                        # 使用 `decode('unicode_escape')` 是一种更健壮的方式来处理多种转义
                        try:
                            detailed_error_info = judge_log_raw.encode('latin1').decode('unicode_escape')
                        except Exception:
                             # 如果解码失败，使用简单的替换作为后备
                            detailed_error_info = judge_log_raw.replace('\\n', '\n').replace('\\"', '"')
                    else:
                        detailed_error_info = "评测机未提供 judgeLog 编译/运行错误信息。"

                    # 2. 结合处理 checkpointResults 作为补充
                    checkpoint_results = result_data.get("checkpointResults", [])
                    if checkpoint_results:
                        failed_checkpoints_log = ["\n\n--- 各测试点评测摘要 ---"]
                        has_failed_checkpoints = False
                        for i, cp_result in enumerate(checkpoint_results):
                            if isinstance(cp_result, list) and len(cp_result) >= 3:
                                cp_status_code, cp_time, cp_memory = cp_result[0], cp_result[1], cp_result[2]
                                cp_status_text = JUDGE_STATUS.get(cp_status_code, f"未知状态码 {cp_status_code}")
                                
                                # 只记录非AC的测试点
                                if cp_status_code != 1:
                                    has_failed_checkpoints = True
                                    log_line = (f"测试点 #{i + 1}: {cp_status_text} "
                                                f"(耗时: {cp_time}ms, 内存: {cp_memory}KB)")
                                    failed_checkpoints_log.append(log_line)
                        
                        if has_failed_checkpoints:
                            detailed_error_info += "\n".join(failed_checkpoints_log)
                    
                    # 3. 将拼接好的详细错误信息放回 result_data
                    result_data["judgeInfo"] = detailed_error_info
                # --- 提取逻辑结束 ---

                if status_code == 1:
                    logging.info(f"  - 耗时: {result_data.get('usedTime')} ms")
                    logging.info(f"  - 内存: {result_data.get('usedMemory')} KB")
                
                # 在评测结束时，统一打印最终的详细信息（如果有）
                if result_data.get("judgeInfo"):
                     logging.info(f"详细评测信息:\n{result_data.get('judgeInfo')}")
                
                logging.info("-" * 50)
                return result_data
        else:
            logging.warning("  查询失败或数据格式不符，稍后重试...")
        time.sleep(2)

    logging.error("❌ 查询超时。")
    return None


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


def run_code_in_sandbox(sandbox_service: Service, minio: Minio, code: str, input_data: str, language: str,
                        bucket_name: str) -> str:
    """在沙箱中运行代码并返回其标准输出"""
    lang_ext = ".cpp" if "C++" in language else ".py"
    source_filename = f"main{lang_ext}"
    sandbox_template = LANGUAGE_TO_SANDBOX_TEMPLATE.get(language)
    if not sandbox_template:
        return f"[ERROR] 不支持的沙箱语言: {language}"

    base_dir = tempfile.mkdtemp()
    source_dir = os.path.join(base_dir, "source")
    data_dir = os.path.join(base_dir, "data")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    try:
        with open(os.path.join(source_dir, source_filename), "w", encoding="utf8") as f:
            f.write(code)
        with open(os.path.join(data_dir, "input"), "w", encoding="utf8") as f:
            f.write(input_data)

        source_zip = zip_directory_to_bytes(source_dir)
        data_zip = zip_directory_to_bytes(data_dir)

        source_io = minio("write", bucket_name, "source.zip", source_zip).result()
        data_io = minio("write", bucket_name, "data.zip", data_zip).result()

        res = sandbox_service(
            source_file=source_io, data_file=data_io,
            output_file={"bucket": bucket_name, "object_name": "output.zip"},
            execution_timeout=5, sandbox_template=sandbox_template
        ).result()

        if res.get('status') != 'success':
            return f"[SANDBOX_ERROR] {res.get('message', '未知沙箱错误')}"

        output_zip_bytes = minio("read", bucket_name, "output.zip").result()
        if output_zip_bytes:
            unzip_bytes_to_directory(output_zip_bytes, output_dir, overwrite=True)
            output_file_path = os.path.join(output_dir, "output")
            if os.path.exists(output_file_path):
                with open(output_file_path, "r", encoding="utf8") as f:
                    return f.read()
        return "[NO_OUTPUT]"
    finally:
        shutil.rmtree(base_dir)


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


def debug_and_fix_with_llm(problem_details: dict, buggy_code: str, failed_case_input: str, expected_output: str,
                           actual_output: str, language: str, model: str, user_hint: str = None):
    """请求LLM分析并修复bug"""
    logging.info("🤖 正在请求 AI 分析并修复代码...")

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
--- 人类开发者的提示 ---
{user_hint}
--- 提示结束 ---
"""
    prompt += f"""
--- 有问题的代码 ---
```{language.lower()}
{buggy_code}
--- 有问题的代码结束 ---
请在'thought'部分详细分析错误的原因，然后在'code'部分提供完整的、修正后的代码。
"""
    try:
        llm = LLM(model)
        response = llm(prompt, structured_output=SolutionOutput.model_json_schema()).result()
        structured_data = response.get("structured_output")
        if structured_data and structured_data.get("code"):
            logging.info("✅ AI 已生成修正后的代码。")
            return structured_data.get("code")
        logging.error("❌ AI 未能生成有效的修正代码。将返回原始代码。")
        return buggy_code
    except Exception as e:
        logging.critical(f"❌ 请求 AI 修复代码时发生错误: {e}")
        return buggy_code

def generate_test_cases_with_llm(problem_details: dict, llm_model: str) -> List[TestCase]:
    """
    【新】调用LLM动态生成测试用例，不再依赖模板。
    """
    logging.info("🚀 正在通过 LLM 动态生成测试用例...")

    # 1. 构建 Prompt
    prompt = f"""
[SYSTEM]
你是一位顶级的软件测试专家和算法竞赛题目分析师。你的任务是根据给定的编程题目描述，生成一套高质量、全面的测试用例。

[USER]
请为以下编程题目生成测试用例。

--- 题目描述 ---
{problem_details['full_markdown_description']}
--- 题目描述结束 ---

请遵循以下要求生成测试用例：
1.  **全面性**: 覆盖以下所有类型：
    *   **基础用例 (basic)**: 正常、典型的输入。
    *   **边界用例 (boundary)**: 关键边界值，如0, 1, -1, 空输入, 数组/字符串为空或只有一个元素等。
    *   **极值用例 (edge)**: 根据题目描述中的数据范围，生成最大值、最小值等极端情况。
2.  **数量**: 每种类型至少生成3-5个有代表性的测试用例。
3.  **格式**: 必须严格按照下面的JSON数组格式返回，不要包含任何额外的解释、代码块标记或其他文字。

JSON格式示例:
[
  {{
    "input_data": "输入数据字符串，完全符合题目输入格式",
    "expected_output": "期望输出字符串，完全符合题目输出格式",
    "description": "对这个测试用例的简短描述",
    "case_type": "basic"
  }}
]
"""

    # 2. 定义期望的 JSON Schema 输出结构
    TestCaseSchema = {
        "title": "GeneratedTestCases",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "input_data": {"type": "string"},
                "expected_output": {"type": "string"},
                "description": {"type": "string"},
                "case_type": {"type": "string", "enum": ["basic", "boundary", "edge"]}
            },
            "required": ["input_data", "expected_output", "description", "case_type"]
        }
    }

    # 3. 异步调用 LLM 算子并等待结果
    try:
        logging.info("⏳ 正在调度并等待 LLM 生成任务...")
        llm = LLM(llm_model)
        future = llm(prompt, structured_output=TestCaseSchema)
        response = future.result()
        llm_results = response.get("structured_output", [])
        if not llm_results:
            raise ValueError("LLM 返回的结构化输出为空。")

        # 4. 将结果解析为 TestCase 对象列表
        test_cases = []
        for result in llm_results:
            test_cases.append(TestCase(**result))
        
        logging.info(f"✅ 成功由 LLM 生成 {len(test_cases)} 个测试用例。")
        return test_cases
        
    except Exception as e:
        logging.error(f"❌ 使用 LLM 生成测试用例时发生错误: {e}")
        logging.critical(traceback.format_exc())
        return [] # 返回空列表表示失败

def pairwise_testing_mode(problem_details: dict, code_to_test: str, llm_model: str, language: str):
    """
    【最终整合版】执行对拍测试，直接调用 LLM 动态生成测试用例，并包含完整的调试修复循环。
    """
    logging.info("=" * 50)
    logging.info("⚔️ 已达到最大尝试次数，进入对拍（Pairwise Testing）模式 ⚔️")
    logging.info("=" * 50)

    brute_force_code = generate_brute_force_solution(problem_details, llm_model, language)
    if not brute_force_code:
        logging.error("无法进行对拍，因为未能生成暴力解法。")
        return

    # --- 核心：直接调用 LLM 生成测试用例 ---
    test_cases = generate_test_cases_with_llm(problem_details, llm_model)[:DUIPAI_COUNT]
    
    if not test_cases:
        logging.error("未能生成任何测试用例，对拍流程无法继续。")
        return

    # 为了方便观察，我们格式化并打印它们
    def format_cases_for_log(cases: List[TestCase]) -> str:
        output = ["🧪 LLM 动态生成的测试用例"]
        output.append("=" * 40)
        case_groups = {}
        for case in cases:
            case_groups.setdefault(case.case_type, []).append(case)
        
        type_names = { "basic": "📝 基础用例", "boundary": "🎯 边界用例", "edge": "⚡ 极值用例" }
        for case_type, cases_in_group in case_groups.items():
            output.append(f"\n{type_names.get(case_type, case_type)}:")
            for i, case in enumerate(cases_in_group, 1):
                # 对输入输出进行截断，避免打印过长
                input_preview = (case.input_data[:70] + '...') if len(case.input_data) > 70 else case.input_data
                output_preview = (case.expected_output[:70] + '...') if len(case.expected_output) > 70 else case.expected_output
                output.append(f"  {i}. {case.description} -> 输入: `{input_preview}`, 期望输出: `{output_preview}`")
        return "\n".join(output)
    
    logging.info(format_cases_for_log(test_cases))
    # --- 生成结束 ---

    # --- Minio 初始化 ---
    sandbox = Service("code-sandbox")
    ctx = get_context()
    minio_client = ctx.minio
    bucket_name = f"duipai-{str(uuid.uuid4())[:8]}"
    
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
        logging.info(f"✅ 成功创建用于对拍的 Minio 存储桶: {bucket_name}")
    except Exception as e:
        logging.error(f"❌ 创建 Minio 存储桶失败: {e}")
        return
    
    minio_operator = Minio()
    
    # --- 调试修复循环 ---
    current_code = code_to_test
    debug_attempt = 0
    all_passed = False

    while debug_attempt < MAX_DEBUG_ATTEMPTS:
        logging.info(f"\n--- 调试修复循环: 第 {debug_attempt + 1}/{MAX_DEBUG_ATTEMPTS} 轮 ---")
        all_passed = True
        
        for i, case in enumerate(test_cases):
            logging.info(f"  -> 测试用例 #{i + 1}/{len(test_cases)}: {case.description}")
            
            std_output = run_code_in_sandbox(sandbox, minio_operator, brute_force_code, case.input_data, language, bucket_name)
            my_output = run_code_in_sandbox(sandbox, minio_operator, current_code, case.input_data, language, bucket_name)

            if std_output.strip() != my_output.strip():
                all_passed = False
                logging.error("❌ 对拍发现错误！")
                logging.error(f"  - 输入:\n{case.input_data}")
                logging.error(f"  - 标准输出 (Expected):\n{std_output}")
                logging.error(f"  - 你的输出 (Got):\n{my_output}")

                # --- 用户交互与自动修复 ---
                user_choice = input(
                    "\n请选择操作：[1] 让AI自动修复 [2] 为AI提供提示后修复 [3] 手动修改代码 [4] 放弃调试\n> "
                ).strip()

                if user_choice == '1':
                    current_code = debug_and_fix_with_llm(problem_details, current_code, case.input_data, std_output, my_output, language, llm_model)
                elif user_choice == '2':
                    hint = input("请输入你的提示信息：\n> ")
                    current_code = debug_and_fix_with_llm(problem_details, current_code, case.input_data, std_output, my_output, language, llm_model, user_hint=hint)
                elif user_choice == '3':
                    current_code = get_manual_code_input()
                else:
                    logging.info("用户选择放弃调试。")
                    # 在退出前尝试清理资源
                    try:
                        objects = minio_client.list_objects(bucket_name, recursive=True)
                        minio_client.remove_objects(bucket_name, [o.object_name for o in objects])
                        minio_client.remove_bucket(bucket_name)
                    except Exception as e:
                        logging.warning(f"放弃调试时清理Minio存储桶出错: {e}")
                    return
                break # 跳出内层 for 循环，用新代码从第一个用例开始重新测试

        if all_passed:
            logging.info("🎉🎉🎉 恭喜！代码已通过所有对拍测试用例！")
            break # 跳出外层 while 循环

        debug_attempt += 1

    if not all_passed:
        logging.error(f"达到最大调试次数 ({MAX_DEBUG_ATTEMPTS})，仍未修复所有问题。")

    # --- 最终清理 ---
    try:
        logging.info(f"正在清理并删除 Minio 存储桶: {bucket_name}...")
        objects = minio_client.list_objects(bucket_name, recursive=True)
        # list_objects 返回的是一个迭代器，需要转换为列表
        object_names = [obj.object_name for obj in objects]
        if object_names:
            errors = minio_client.remove_objects(bucket_name, object_names)
            for error in errors:
                logging.warning(f"删除 Minio 对象时出错: {error}")
        minio_client.remove_bucket(bucket_name)
        logging.info(f"✅ 成功清理 Minio 存储桶。")
    except Exception as e:
        logging.error(f"❌ 清理 Minio 存储桶时发生严重错误: {e}")

# --- 主执行流程 __main__  ---
def main():
    """主执行函数，采用“计划-编码-反思-对拍调试”的先进工作流"""
    # 1. 初始化和登录
    username = os.getenv("SDUOJ_USERNAME", "202300130111")
    password = os.getenv("SDUOJ_PASSWORD", "1517287203Syx")

    if password == "您的密码":
        password = getpass.getpass("请输入您的 SDUOJ 密码: ")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'{BASE_URL}/v2/problem/{PROBLEM_CODE}',
    })

    logging.info("-" * 50)
    logging.info(f"准备开始自动化流程，目标题目: {PROBLEM_CODE}")
    logging.info("-" * 50)

    # 使用 Context 管理连接和任务ID
    with Context(task_id=f"sduoj-solver-{str(uuid.uuid4())[:8]}",router=1234567890):
        if not login(session, username, password):
            return

        problem_details = get_problem_details(session, PROBLEM_CODE)
        if not problem_details:
            return

        # 2. 生成一次性的高级解题计划
        plan, tokens_for_plan = generate_plan_with_llm(problem_details, LLM_MODEL_FOR_ANALYSIS, SUBMISSION_LANGUAGE)
        if not plan:
            logging.error("❌ 未能生成解题计划，终止流程。")
            return

        # 3. 初始化常规提交循环的状态
        submission_history = []
        total_tokens_used = tokens_for_plan
        solution_accepted = False

        # 4. 开始常规的“编码-提交-反思”循环
        while len(submission_history) < MAX_ATTEMPTS:
            attempt_num = len(submission_history) + 1
            logging.info("-" * 50)
            logging.info(
                f"🚀 开始第 {attempt_num}/{MAX_ATTEMPTS} 次常规提交尝试... (已消耗 Tokens: {total_tokens_used}/{TOTAL_TOKEN_LIMIT})")
            logging.info("-" * 50)

            if total_tokens_used >= TOTAL_TOKEN_LIMIT:
                logging.warning(f"已达到TOKEN消耗上限 ({TOTAL_TOKEN_LIMIT})，停止常规尝试。")
                break

            # 根据计划和历史记录生成代码
            solution_code, thought, tokens_this_call = generate_solution_with_llm(
                problem_details, plan, LLM_MODEL_FOR_ANALYSIS,
                SUBMISSION_LANGUAGE, submission_history, attempt_num
            )
            total_tokens_used += tokens_this_call

            if not solution_code:
                logging.error("🧠 LLM未能生成有效代码，终止本次尝试。")
                # 即使代码生成失败，也记录一次尝试
                submission_history.append({
                    "code": "", "thought": thought or "代码生成失败",
                    "result_text": "Code Generation Failed", "error_info": "LLM did not return valid code."
                })
                continue

            # 自动提交，如需手动确认可取消下行注释
            # confirm = input("确认提交吗? (y/n): ").lower()
            # if confirm != 'y':
            #     logging.info("操作已由用户取消。")
            #     break

            submission_id = submit_solution(session, problem_details['id'], solution_code, SUBMISSION_LANGUAGE)
            if not submission_id:
                logging.warning("提交失败，记录错误并进入下一次尝试...")
                submission_history.append({
                    "code": solution_code, "thought": thought,
                    "result_text": "Submission API Failed",
                    "error_info": "API call to submit the code failed."
                })
                continue

            result_data = check_submission_status(session, submission_id)

            if result_data:
                status_code = result_data.get("judgeResult")
                status_text = JUDGE_STATUS.get(status_code, f"Unknown Status ({status_code})")

                if status_code == 1:  # Accepted
                    logging.info("🏆🎉 恭喜！问题已解决！")
                    solution_accepted = True
                    break  # 成功则跳出循环

                logging.warning(f"😔 本次尝试未通过，结果: {status_text}。正在记录失败信息并准备重试...")

                error_info = result_data.get("judgeInfo", "评测机未提供具体的错误信息。")
                submission_history.append(
                    {"code": solution_code, "thought": thought, "result_text": status_text, "error_info": error_info})
            else:
                logging.error("无法获取评测结果，终止尝试。")
                break

        # 5. 检查是否需要进入对拍调试模式
        if not solution_accepted and submission_history and submission_history[-1]['code']:
            # 获取最后一次失败的代码作为“待测解”
            last_failed_code = submission_history[-1]['code']
            # 启动对拍调试流程
            pairwise_testing_mode(
                problem_details,
                last_failed_code,
                LLM_MODEL_FOR_ANALYSIS,
                SUBMISSION_LANGUAGE
            )
        elif solution_accepted:
            logging.info("代码已通过OJ评测，无需进入对拍模式。")
        else:
            logging.warning("未能成功生成或提交任何有效代码，无法进入对拍模式。")


if __name__ == "__main__":
    start_time = time.time()
    try:
        main()
    except Exception as e:
        logging.critical(f"\n❌ 脚本在执行过程中发生致命错误: {e}")
        logging.critical(traceback.format_exc())
    finally:
        end_time = time.time()
        logging.info(f"\n总耗时：{end_time - start_time:.2f} 秒")
        logging.info(f"完整的操作日志已保存在: {log_filename}")
        logging.info("自动化流程执行完毕。")