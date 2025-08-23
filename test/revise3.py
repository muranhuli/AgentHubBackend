import requests
import json
import os
import getpass
import traceback
import time
import logging
import re
import uuid
import numpy as np
import logging
import pymysql
import tempfile
import shutil

from datetime import datetime
from bs4 import BeautifulSoup
from coper.Minio import Minio
from io import BytesIO
from core.Computable import Computable
from coper.Embedding import Embedding  # 导入 Embedding 类
from coper.VectorDB import VectorDB
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import List
from typing import Optional,List,Dict,Any
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
# 导入已有的 coper 模块
from coper.LLM import LLM
from core.Context import Context,get_context
from coper.Service import Service
from core.Utils import zip_directory_to_bytes, unzip_bytes_to_directory

#结构化输出定义
@dataclass
class TestCase(BaseModel):
    """测试用例数据结构"""
    input_data: str = Field(..., description="测试用例的输入数据。")
    expected_output: str = Field(..., description="对应输入的预期正确输出。")
    description: str = Field(..., description="简要说明该测试用例旨在检查的边界或特定情况。")
    case_type: str = Field(..., description="用例类型，必须是 'basic', 'boundary', 或 'edge' 之一。")

# 【新增】用于包裹测试用例列表的 Pydantic 模型
class TestCaseList(BaseModel):
    """A list of test cases."""
    test_cases: List[TestCase] = Field(..., description="包含多个测试用例的列表。")

class SolutionOutput(BaseModel):
    thought: str = Field(..., description="一步步解释代码背后逻辑的思考过程。")
    code: str = Field(..., description="用于解决问题的完整、可运行的源代码。")

class ErrorTypeAnalysisOutput(BaseModel):
    error_type: str = Field(..., description="The type of the error, must be 'conceptual', 'implementation', or 'unknown'.")
    reasoning: str = Field(..., description="A detailed explanation for the classification.")

class CounterExampleOutput(BaseModel):
    input_data: str = Field(..., description="A specific input that demonstrates the conceptual error.")
    expected_output: str = Field(..., description="The correct output for the generated input.")

class ImplementationAnalysisOutput(BaseModel):
    analysis: str = Field(..., description="A detailed analysis of the implementation error.")
    suggestion: str = Field(..., description="A concrete suggestion for fixing the code, can be a code snippet or clear instructions.")

class SimplifiedProblemOutput(BaseModel):
    simplified_description: str = Field(..., description="The simplified problem description in pure technical or mathematical markdown format.")

class PossibleErrorsOutput(BaseModel):
    markdown_content: str = Field(..., description="A markdown-formatted text listing and explaining potential errors for the problem.")

class SolutionDescriptionOutput(BaseModel):
    description: str = Field(..., description="A concise description of the solution's core logic, algorithm, data structures, and complexity.")

# --- 1. 配置信息 ---
BASE_URL = "https://oj.qd.sdu.edu.cn"
PROBLEM_CODE = "SDUOJ-1204"
LLM_MODEL_FOR_ANALYSIS = "volcengine/doubao-seed-1-6-250615"  # 使用 DeepSeek Chat 模型进行题目分析
# SUBMISSION_LANGUAGE = "Python"
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
# 定义存放所有解决方案的目录名
SOLUTIONS_DIR = "solutions"
# SUBMISSION_LANGUAGE = "C++"
# --- Token 限制配置 ---
MAX_PROMPT_TOKENS = 8000  # 单次询问的Prompt Token上限 (估算)
TOTAL_TOKEN_LIMIT = 50000  # 整个解题过程的总Token消耗上限
JUDGE_STATUS = {
    -4: "Queueing",
    -3: "Compiling",
    -2: "Judging",
    -1: "End (Internal System Status, may indicate completion)",
    0: "Pending",
    1: "Accepted",
    2: "Time Limit Exceeded",
    3: "Memory Limit Exceeded",
    4: "Runtime Error",
    5: "System Error",
    6: "Wrong Answer",
    7: "Presentation Error",
    8: "Compilation Error",
    9: "Output Limit Exceeded",
    99: "Cancelled"
}
# 最大尝试次数
MAX_ATTEMPTS = 2  
MAX_DEBUG_ATTEMPTS = 3  # 对拍模式下的最大调试修复次数
DUIPAI_COUNT = 20  # 对拍测试用例数量
LANGUAGE_TO_SANDBOX_TEMPLATE = {
    "C++14": "gcc-13.3-cpp-std_14-O2",
    "C++17": "gcc-13.3-cpp-std_17-O2",
    "C++20": "gcc-13.3-cpp-std_20-O2",
    "Python3.11": "python-3.11",
    "Python3.12": "python-3.12",
}
# --- 知识库配置 ---
KNOWLEDGE_MINIO_ENDPOINT = os.getenv("KNOWLEDGE_MINIO_ENDPOINT", "10.102.34.150:19001")
KNOWLEDGE_MINIO_ACCESS_KEY = os.getenv("KNOWLEDGE_MINIO_ACCESS_KEY", "minio")
KNOWLEDGE_MINIO_SECRET_KEY = os.getenv("KNOWLEDGE_MINIO_SECRET_KEY", "nQuvqL4lWopVBDo5Slr57J0aWsOVV2omPgY8Ob+Ickk")
KNOWLEDGE_MINIO_BUCKET = os.getenv("KNOWLEDGE_MINIO_BUCKET", "knowledge-base")

MILVUS_HOST = "10.102.34.150"
MILVUS_PORT = "19530"
MILVUS_COLLECTION_NAME = "problem_embeddings"

# --- 日志记录配置 ---
log_filename = f"sduoj_solver_run_{PROBLEM_CODE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
#调用LLM判断错误类型 （概念性、实现型）
def judge_error_type_with_llm(problem_desc: str, student_code: str,  llm_model: str) -> dict:
    """
    使用 LLM 判断学生的错误是概念性错误还是实现性错误。
    返回格式: {"error_type": "conceptual" 或 "implementation" 或 "unknown", "reasoning": "LLM 的分析", "raw_feedback": "原始评测信息"}
    """
    logging.info("🤖 LLM: 正在分析错误类型（概念性 vs 实现性）...")

    
    # 构建给 LLM 的 Prompt
    prompt = f"""
[SYSTEM]
你是一位顶级的竞赛编程导师。你将分析一个学生提交的、因逻辑错误而判为不正确的代码。
你的任务是根据问题陈述、学生代码和评测反馈，判断错误是源于核心算法/逻辑的缺陷（概念性错误），还是编码实现细节的失误（实现性错误）。

[问题陈述]
{problem_desc}

[学生代码]
```{SUBMISSION_LANGUAGE.lower()}
{student_code}
[任务]
分析学生代码和评测反馈。
判断主要问题是出现在基本方法（例如，选择了错误的算法、逻辑不正确）还是代码的实现方式（例如，越界错误、变量使用不当、导致运行时错误的语法问题，但逻辑本身是健全的）。
提供清晰的分类解释。
[输出格式]
错误类型: <conceptual 或 implementation>
原因分析: <你的详细解释>
"""
    try:
        llm = LLM(model=llm_model)
        response = llm(prompt, structured_output=ErrorTypeAnalysisOutput.model_json_schema()).result()
        structured_data = response.get("structured_output")
        if not structured_data:
            raise ValueError("LLM did not return a valid structured analysis.")
        
        error_type = structured_data.get("error_type", "unknown").lower()
        if error_type not in ["conceptual", "implementation"]:
            error_type = "unknown"

        reasoning = structured_data.get("reasoning", "LLM did not provide a reasoning.")
        
        logging.info(f"LLM 错误类型分类: {error_type.upper()}，原因: {reasoning[:100]}...")
        return {"error_type": error_type, "reasoning": reasoning}

    except Exception as e:
        logging.error(f"❌ 使用 LLM 分析错误类型时出错: {e}")
        return {"error_type": "unknown", "reasoning": f"LLM analysis failed: {e}"}

#概念性错误（思路错误），生成反例
def generate_counter_example_with_llm(problem_desc: str, student_code: str, error_analysis: dict, llm_model: str) -> str:
    """
    当 LLM 判断为概念性错误时，使用 LLM 生成一个能暴露此概念性错误的测试用例（反例）。
    返回一个包含输入和正确输出的字符串。
    """
    logging.info("🤖 LLM: 正在为概念性错误生成反例...")
    
    # 构建给 LLM 的 Prompt，强调任务和上下文
    prompt = f"""
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
基于问题陈述和已识别出的概念性错误，设计一个特定的输入测试用例。
确定该输入对应的正确输出。
清晰地呈现输入和正确输出。
[输出格式]
输入:
<你生成的输入>
正确输出:
<你生成的输入对应的正确输出>
"""
    try:
        llm = LLM(model=llm_model)
        response = llm(prompt, structured_output=CounterExampleOutput.model_json_schema()).result()
        structured_data = response.get("structured_output")
        if not structured_data:
            return "LLM未能成功生成反例。"

        generated_input = structured_data.get("input_data", "无法生成输入。")
        correct_output = structured_data.get("expected_output", "无法确定正确输出。")
        
        counter_example_info = f"LLM 生成的反例:\n输入:\n{generated_input}\n正确输出:\n{correct_output}\n"
        logging.info(counter_example_info)
        return counter_example_info

    except Exception as e:
        logging.error(f"❌ 使用 LLM 生成反例时出错: {e}")
        return f"LLM 在生成反例时出错: {e}"

#实现性错误 调用llm实际分析
def analyze_implementation_error_with_llm(problem_desc: str, student_code: str, error_analysis: dict,llm_model: str) -> str:
    """
    当 LLM 判断为实现性错误时，使用 LLM 分析具体的实现问题并提供修复建议。
    返回一个包含分析和建议的字符串。
    """
    logging.info("🤖 LLM: 正在分析实现性错误并提供修复建议...")
    prompt_parts = [
        "[SYSTEM]",
        "你是一位顶级的竞赛编程导师。学生的代码因实现性错误而被判错误，但其核心逻辑是健全的。",
        "你的任务是精确地指出代码中存在错误的具体实现细节，并提供清晰、可操作的修复建议。",
        "",
        "[问题陈述]",
        problem_desc,
        "",
        "[学生代码]",
        f"```{SUBMISSION_LANGUAGE.lower()}\n{student_code}\n```",
        "",
        "[LLM 对实现性错误的分析]",
        f"LLM 先前已将错误类型判断为实现性，原因为：{error_analysis.get('reasoning', '未提供原因。')}",
        "",
        "[任务]",
        "1. 结合问题陈述和已识别的实现性错误，仔细检查学生代码。",
        "2. 找出包含 Bug 的确切代码行或代码段。",
        "3. 解释为什么它错了。",
        "4. 提供修正后的代码片段或清晰的修复说明。",
        "5. 如果存在多个问题或细微之处，请一并说明。",
        "",
        "建议修复:",
        "<修正后的代码片段或具体说明>"
    ]

    prompt = "\n".join(prompt_parts)

    try:
        llm = LLM(model=llm_model)
        response = llm(prompt, structured_output=ImplementationAnalysisOutput.model_json_schema()).result()
        structured_data = response.get("structured_output")
        
        if not structured_data:
            raise ValueError("LLM did not return a valid structured analysis.")
        
        analysis = structured_data.get("analysis", "LLM 未提供具体分析。")
        suggestion = structured_data.get("suggestion", "LLM 未提供具体修复建议。")
        
        result = {
            "error_type": "implementation",
            "reasoning": error_analysis.get('reasoning'),
            "implementation_analysis": analysis,
            "fix_suggestions": suggestion
        }
        logging.info(f"实现错误分析:\n{analysis}\n\n建议修复:\n{suggestion}")
        return result

    except Exception as e:
        logging.error(f"❌ 使用 LLM 分析实现错误时出错: {e}")
        return {
            "error_type": "implementation", "reasoning": "LLM analysis failed",
            "implementation_analysis": str(e), "fix_suggestions": "N/A"
        }
# 初始化嵌入模型
# with Context(task_id="embedding-init"):
#     embedding_model = Embedding()

# 内存缓存
embedding_cache = {}

@staticmethod
def _get_embedding(text: str) -> np.ndarray:
    """ 向量"""
    emb = Embedding()
    result =emb(text).result()
    return result
class KnowledgeBase:
    """统一封装 MinIO + Milvus 的知识库管理器"""
    def __init__(self):
        self.bucket_name = KNOWLEDGE_MINIO_BUCKET
        self.vdb = VectorDB()
        self.minio = Minio()
        self.minio("make_bucket", self.bucket_name)

        self.solution_collection_name = MILVUS_COLLECTION_NAME
        self.error_collection_name = "problem_errors"
        # if utility.has_collection(self.solution_collection_name, using="agent_vectorDB"):
        #     logging.warning(f"Collection '{self.solution_collection_name}' 已存在，正在删除...")
        #     utility.drop_collection(self.solution_collection_name, using="agent_vectorDB")
        # if utility.has_collection(self.error_collection_name, using="agent_vectorDB"):
        #     logging.warning(f"Collection '{self.error_collection_name}' 已存在，正在删除...")
        #     utility.drop_collection(self.error_collection_name, using="agent_vectorDB")
        logging.info(f"📦 使用知识库存储桶: {self.bucket_name}")
        logging.info("📚 知识库已初始化 (Milvus & MinIO)")

        dimension = 1024
        self.vdb("create_collection", collection_name=self.solution_collection_name, dimension=dimension).result()
        self.vdb("create_collection", collection_name=self.error_collection_name, dimension=dimension).result()
        self.vdb("create_index", collection_name=self.solution_collection_name)
        self.vdb("create_index", collection_name=self.error_collection_name)
        logging.info("📚 Milvus 向量索引已建立。")
        
    # ---------- MinIO 基础调用 ----------
    def _upload(self, object_name: str, content: str | bytes) -> str:
        self.minio("write", self.bucket_name, object_name, content)
        return object_name

    # def _download(self, object_name: str) -> Optional[str]:
    #     # data = self.minio("read", self.bucket_name, object_name)
    #     # return data.decode("utf-8") 
    #     # if data else None
    #     # 1. 调用 minio("read", ...) 时，会返回一个 ComputableResult 对象
    #     result_wrapper = self.minio("read", self.bucket_name, object_name)

    #     # 2. 从 ComputableResult 对象中获取实际数据。
    #     try:
    #         data = result_wrapper.result()
    #         # 检查 data 是否是 bytes
    #         if isinstance(data, bytes):
    #             return data.decode("utf-8")
    #         elif data is None: # MinIO read 可能返回 None 如果文件不存在
    #             return None
    #         else:
    #             # 如果 data 不是 bytes，可能是其他类型，需要检查
    #             logging.error(f"MinIO read operation returned unexpected type: {type(data)}")
    #             return None
    #     except AttributeError
    #         logging.error("ComputableResult object does not have .result() attribute. Trying direct access.")
    #         if hasattr(result_wrapper, 'data') and isinstance(result_wrapper.data, bytes):
    #              data = result_wrapper.data
    #              return data.decode("utf-8")
    #         elif result_wrapper is None: # MinIO read 可能返回 None
    #              return None
    #         else:
    #              logging.error(f"Failed to extract bytes data from MinIO read result: {result_wrapper}")
    #              return None
    #     except Exception as e:
    #         logging.error(f"Error decoding MinIO data for object '{object_name}': {e}")
    #         return None
        

    def _download(self, object_name: str) -> Optional[str]:
        # 调用 Minio.compute("read", ...)
        # 根据 Minio.read() 的定义，返回值是 bytes, str, or None
        # 并且 Minio.compute() 是同步的，直接返回 Minio.read() 的结果
        # 所以 result_wrapper 应该是 bytes, str, or None
        data = self.minio("read", self.bucket_name, object_name)

        if isinstance(data, bytes):
            # 如果 minio.read 返回 bytes，则 decode 成 utf-8
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                logging.error(f"Failed to decode bytes data from MinIO for object '{object_name}' as UTF-8.")
                # 如果不是 utf-8 编码，可以尝试其他编码，或者返回原始 bytes
                return None # 或者返回 data.decode('latin-1') 或其他
        elif isinstance(data, str):
            # 如果 minio.read 返回的已经是 str ，则直接返回
            return data
        elif data is None:
            # 如果 minio.read 返回 None ，则返回 None
            return None
        else:
            # 如果返回了其他意外的类型
            logging.error(f"MinIO read operation for '{object_name}' returned unexpected type: {type(data)}")
            return None

    # ---------- 追加内容 ----------
    def append_to_solve_md(self, problem_id: str, content: str) -> str:
        key = f"{problem_id}/solve.md"
        existing = self._download(key) or ""
        return self._upload(key, f"{existing}\n\n{content}")

    def append_to_error_md(self, problem_id: str, content: str) -> str:
        key = f"{problem_id}/error.md"
        existing = self._download(key) or ""
        return self._upload(key, f"{existing}\n\n{content}")

    # ---------- Milvus 搜索 ----------
    def search_solution(self, vector: List[float], problem_id: str, top_k: int = 5):
        return self.vdb(
            "search_vector",
            collection_name=self.solution_collection_name,
            query_vector=vector,
            top_k=top_k
        ).result()

    def search_error(self, vector: List[float], problem_id: str, top_k: int = 5):
        return self.vdb(
            "search_vector",
            collection_name=self.error_collection_name,
            query_vector=vector,
            top_k=top_k
        ).result()

    # ---------- 题面 ----------
    def save_problem_simplified(self, problem_id: str, content: str) -> str:
        return self._upload(f"{problem_id}/problem_s.md", content)

    def get_problem_simplified(self, problem_id: str) -> Optional[str]:
        return self._download(f"{problem_id}/problem_s.md")

    # ---------- 解法 ----------
    def add_solution(self, problem_id: str, desc: str, code: str) -> str:
        solution_id = str(uuid.uuid4())
        content = f"## 解法 ID: {solution_id}\n### 描述\n{desc}\n### 代码\n```{SUBMISSION_LANGUAGE.lower()}\n{code}\n```"
        minio_key = f"{problem_id}/solutions/{solution_id}.md"
        self._upload(minio_key, content)

        # 生成 embedding
        embedding_model = Embedding()
        vector = embedding_model.compute(f"{desc}\n{code}")
        vectors = [vector]

        # 插入 Milvus
        self.vdb(
            "insert_vector",
            collection_name=self.solution_collection_name,
            vectors=vectors,
            contents=[content],
            labels=["solution"]
        ).result()

        # 更新 solve.md
        self.append_to_solve_md(problem_id, f"## 解法 ID: {solution_id}\n**描述**: {desc[:200]}...\n[查看详情]({minio_key})")
        logging.info(f"✅ 解法已添加: {solution_id}")
        return solution_id

    def search_similar_solutions(self, problem_id: str, embedding: list, top_k: int = 5) -> list:
        return self.search_solution(embedding, problem_id, top_k)

    # ---------- 错误 ----------
    def add_error_sample(self, problem_id: str, desc: str, code: str) -> str:
        error_id = str(uuid.uuid4())
        content = f"## 错误 ID: {error_id}\n### 描述\n{desc}\n### 代码\n```{SUBMISSION_LANGUAGE.lower()}\n{code}\n```"
        minio_key = f"{problem_id}/errors/{error_id}.md"
        self._upload(minio_key, content)

        embedding_model = Embedding()
        vector = embedding_model.compute(f"{desc}\n{code}")
        vectors = [vector]

        self.vdb(
            "insert_vector",
            collection_name=self.error_collection_name,
            vectors=vectors,
            contents=[content],
            labels=["error"]
        ).result()

        self.append_to_error_md(problem_id, f"## 错误 ID: {error_id}\n**描述**: {desc[:200]}...\n[查看详情]({minio_key})")
        logging.info(f"✅ 错误样本已添加: {error_id}")
        return error_id

    def search_similar_errors(self, problem_id: str, embedding: list, top_k: int = 5) -> list:
        return self.search_error(embedding, problem_id, top_k)

#提炼代码solution
def extract_solution_from_code(code: str, problem_desc: str ,llm_model:str) -> dict:
    """
    从学生代码中提取解法描述
    返回格式: {"description": "解法描述", "code": "代码"}
    """
    prompt = f"""
[任务]
你是一个解法提取器，请从学生代码中提取解法描述。

[输入]
1. 问题描述:
{problem_desc}

2. 学生代码:
```{SUBMISSION_LANGUAGE.lower()}
{code}
[要求]

提取解法的核心思路，包括使用的算法、数据结构、优化技巧等
描述时间复杂度和空间复杂度
语言简洁，不超过200字
不要包含代码本身
[输出格式]
解法描述: <描述文本>
"""
    try:
        llm = LLM(model=llm_model)
        response = llm(prompt, structured_output=SolutionDescriptionOutput.model_json_schema()).result()
        structured_data = response.get("structured_output")
    
        if not structured_data or not structured_data.get("description"):
            raise ValueError("LLM did not return a valid description.")
        
        return {
            "description": structured_data.get("description"),
            "code": code
        }
    except Exception as e:
        logging.error(f"❌ 提取解法失败: {e}")
        return {"description": "解法提取失败", "code": code}

        #OJClient
#登录到oj  --与oj交互模块
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

#获取题目信息  --与oj交互模块
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

def generate_possible_errors(problem_desc, llm_model: str) -> str:
    """
    生成针对特定题目可能出现的错误类型和具体描述。
    
    :param problem_description: 题目描述（简化或完整描述）
    :param model_name: 使用的LLM模型名称
    :return: 错误描述的Markdown文本
    """
    logging.info("🔍 LLM: 正在生成潜在错误分析...")
    
    # 构建提示词
    prompt = f"""
[SYSTEM]
你是一位经验丰富的竞赛编程教练，请分析给定编程问题，指出解题者可能犯的常见错误类型及具体原因。

[问题描述]
{problem_desc}

[任务]
1. 分析题目中的难点和陷阱
2. 分类列出可能的错误类型（概念性错误/实现性错误）
3. 为每种错误类型提供：
   a) 错误代码片段示例（伪代码或语言无关）
   b) 错误原因解释
   c) 避免该错误的建议

"""

    try:
        llm = LLM(model=llm_model)
        response = llm(prompt).result()
        content = response.get("content", "")
        logging.debug(f"LLM 潜在错误分析响应:\n{content}")

        # 格式化输出结果
        errors_content = content.strip()
        if not errors_content.startswith("#"):
            errors_content = f"# 潜在错误分析\n\n{errors_content}"

        logging.info("✅ 潜在错误分析生成成功！")
        return errors_content

    except Exception as e:
        logging.error(f"❌ 生成潜在错误分析失败: {e}")
        logging.error(traceback.format_exc())
        return "# 潜在错误分析\n\n生成失败，请手动分析题目难点和常见错误。"

def generate_edge_cases_with_llm(problem_content: str, llm_model: str) -> List[TestCase]:
    """
    【已修复】使用 LLM 根据题目描述生成结构化的边缘测试用例列表。
    返回一个包含 TestCase 对象的列表。
    """
    logging.info("🧪 LLM: 正在生成结构化的边缘测试用例...")

    prompt = f"""
[SYSTEM]
You are an expert test case designer for competitive programming. Your task is to generate a comprehensive set of edge cases for the given problem that could expose potential bugs. Your output must be a JSON object containing a list of test cases.

[USER]
For the problem described below, please perform the following tasks:
1.  Carefully analyze every constraint mentioned in the problem description (e.g., variable ranges, data types, special relationships).
2.  Devise input data that specifically targets these boundaries and extreme conditions.
3.  Generate a list of test cases. For each test case, you must provide:
    a.  `input_data`: The specific input text.
    b.  `expected_output`: The correct expected output for that input.
    c.  `description`: A brief rationale explaining which edge case this test case is designed to check.
    d.  `case_type`: Classify the case as "basic", "boundary", or "edge".

[Problem Description]
{problem_content}
"""
    try:
        llm = LLM(model=llm_model, custom_provider="volcengine")

        # 使用新的 TestCaseList Schema 来获取结构化列表
        response = llm(prompt, structured_output=TestCaseList.model_json_schema()).result()
        structured_data = response.get("structured_output")

        # 检查并访问正确的字段名 "test_cases"
        if not structured_data or "test_cases" not in structured_data or not isinstance(structured_data["test_cases"], list):
            raise ValueError("LLM did not return a valid list of test cases.")

        # 将返回的字典列表转换为 TestCase 对象列表
        # 注意：coper.LLM 的实现可能已经完成了这一步，但这样做更健壮
        test_cases_dicts = structured_data.get("test_cases", [])
        test_cases = [TestCase(**case_dict) for case_dict in test_cases_dicts]
        
        logging.info(f"✅ 成功生成 {len(test_cases)} 个结构化测试用例！")
        return test_cases

    except Exception as e:
        logging.error(f"❌ 生成边缘测试用例失败: {e}")
        # 在失败时返回一个空列表，以保持类型一致性
        return []


#在深度分析模块，简化题面，并保存到problem_s.md
#让ai生成代码，并且如果代码通过评测系统，那么将这个解法加入到solve.md
#同时，让ai列举题目可能出现的几种错误，放到error.md里面
#同时，让ai列举题目可能存在的所有边缘数据，加入到public测试集里面
#如果ai生成的代码一直过不了评测系统，那么需要对拍器+oiwiki辅助ai进行  该部分未完成 
#如果还过不了，人工介入
def generate_problem_simplified(problem_content: str, llm_model: str) -> str:
    """
    生成简化的数学形式题目描述 (problem_s.md)
    """
    logging.info("📝 开始生成简化数学形式的题目描述...")
    
    # 构建提示词
    prompt = f"""
【角色】
你是一名“极简题面生成器”，只输出数学形式，不讲故事。

【输入】
{problem_content}

【任务】
生成一份“纯技术规格”文档，要求：
1. 删除所有背景、故事、情境、示例解释、提示。
2. 用符号表达：输入集合、输出集合、约束条件、数学关系。
3. 必须包含：
   - 变量名及类型
   - 变量上下界
   - 运算/逻辑关系式
4. 禁止出现：
   - 任何自然语言描述
   - 样例输入/输出
   - 解释性文字

"""
    print(prompt)
    exit(0)
    try:
        llm = LLM(model=llm_model, custom_provider="volcengine")
        response = llm(prompt, structured_output=SimplifiedProblemOutput.model_json_schema()).result()
        structured_data = response.get("structured_output")

        if not structured_data or not structured_data.get("simplified_description"):
            raise ValueError("LLM did not return a valid simplified description.")
            
        simplified_content = structured_data.get("simplified_description")
        logging.info("✅ 简化题面生成成功！")
        return simplified_content
    
    except Exception as e:
        logging.error(f"❌ 生成简化题面失败: {e}")
        return problem_content

#生成代码
#根据题面 + 历史失败记录 → 生成新代码 + Thought + Token 用量。
def generate_solution_with_llm(problem_details: dict, model_identifier: str, language: str, submission_history: list,
                               attempt_num: int):
    """
    【已修复无限递归】根据问题详情和所有历史失败尝试，构建一个模仿人类思考模式的Prompt。
    本版本保留了算法列表，并放宽了单次 token 检查。
    """
    logging.info("🤖 准备构建Prompt并调用大模型...")
    problem_description = problem_details.get('simplified_description',
                                              problem_details['full_markdown_description'])

    # 将庞大的算法列表作为背景知识，这部分内容相对固定
    background_knowledge = """
1.  **核心思想**: 选择要使用的主要算法或数据结构，可以从以下方案中选择：

基础算法：枚举、模拟、递归&分治、贪心、排序（选择排序、冒泡排序、插入排序、计数排序、基数排序、快速排序、归并排序、堆排序、桶排序、希尔排序、锦标赛排序、Tim排序）、前缀和&差分、二分、倍增、构造；
搜索算法：DFS、BFS、双向搜索、启发式搜索、A*、迭代加深搜索、IDA*、回溯法、Dancing Licks、Alpha-Beta剪枝、搜索优化
动态规划算法：背包DP、区间DP、DAG上的DP、树形DP、状压DP、数位DP、插头DP、计数DP、动态DP、概率DP、DP套DP、DP优化（单调队列、单调栈优化、，斜率优化、四边形不等式优化、Slope Trick优化、WQS二分、状态设计优化）
字符串算法：字符串匹配、字符串哈希、字典树、前缀算法、KMP算法、Boyer-Moore算法、Z函数、AC自动机、后缀数组、后缀自动机、后缀平衡树、广义后缀平衡树、后缀树、Manacher、回文树、序列自动机、最小表示法、Lyndon分解、Main-Lorentz算法
数学：进位制、位运算、二进制集合操作、平衡三进制、高精度计算、快速幂、置换和排列、互弧度制与坐标系、复数、数论（素数、最大公约数、数论分块、欧拉函数、筛法、Meissel-Lehmer算法、分解质因数、贝祖定理、类欧几里得算法、欧拉算法&费马小定理、乘法逆元、线性同余方程、中国剩余定理、升幂引理、阶乘取模、卢卡斯定理、同余方程、二次剩余、原根、离散对数、剩余、莫比乌斯反演、杜数筛、Powerful Number筛、Min_25筛、洲阁筛、连分数、Stern-Brocot树与Farey序列、二次城、Pell方程）、多项式与生成函数（代数基本定理、快速傅里叶变换、快速数论变换、快速沃尔什变换、Chirp Z变换、多项式牛顿迭代、多项式多点求值|快速插值、多项式初等函数、常系数齐次线性递推、多项式平移|连续点值平移、符号化方法、Lagrange反演、形似幂级数复合|复合逆、普通生成函数、指数生成函数、狄利克雷生成函数）、组合数学（排列组合、抽屉原理、容斥原理、斐波那契数列、错位排列、卡特兰数、斯特林数、贝尔数、伯努利数、Entringer Number、Eulerian Number、分拆数、范德蒙德卷积、Polya计数、图论计数）、线性代数（向量、内积和外积、矩阵、初等变换、行列式、线性空间、线性基、线性映射、特征多项式、对角化、Jordan标准型）、线性规划（单纯形法）、抽象代数（群论、环论、域论、Schreier-Sims算法）、概率论（条件概率与独立性、随机变量、随机变量的数字特征、概率不等式）、博弈论（公平组合游戏、非公平组合游戏）、数值算法（插值、数值积分、高斯消元、牛顿迭代法）、序理论、杨氏矩阵、拟阵、Beriekamp-Massey算法；
数据结构：栈、队列、链表、哈希表、并查集、堆（二叉堆、配对堆、左偏树）、块状数据结构（块状数组、块状链表、树分块、Sqrt Tree）、单调栈、单调队列、ST表、树状数组、线段树（线段树合并&分裂、李超线段树、猫树、区间最值操作&区间历史最值、划分树）、二叉搜索树&平衡树（Treap、Splay树、WBLT、替罪羊树、笛卡尔树、Size Balanced Tree、AVL树、红黑树、左偏红黑树、AA树）、跳表、可持久化数据结构（可持久化线段树、可持久化块状数组、可持久化平衡树、可持久化字典树、可持久化可并堆）、树套树（线段树套线段树、平衡树套线段树、线段树套平衡树、树状数组套权值平衡树、分块套树状数组）、K-D Tree、动态树（Link cut Tree全局平衡二叉树、Euler Tour Tree、Top Tree）、析和树、PQ树、手指树、霍夫曼树；
图论：图的存储、DFS、BFS、树上问题（树的直径、树的中心、最近公共祖先、树链剖分、树上启发式合并、虚树、树分治、动态树分治、AHU算法、树哈希、树上随机游走）、有向无环图、拓扑排序、最短路问题（最短路、差分约束、k短路、同余最短路）、生成树问题（最小生成树、最小树形图、最小直径生成树）、斯坦纳树、拆点、连通性相关（强联通分量、双联通分量、割点和桥、圆方图、点/边连通度）环计数问题、最小环、2-SAT、欧拉图、哈密顿图、二分图、平面图、弦图、图的着色、网络流（最大流、最小流、费用流、上下界网络流、Stoer-Wagner算法）、图的匹配（二分图最大匹配、二分图最大权匹配、一般图最大匹配、一般图最大权匹配）、Prufer序列、矩阵树定理、LGV引理、最大团搜索算法、支配树、图上随机游走；
计算几何：二维计算几何、三维计算几何、距离、Pick定理、三角剖分、凸包、扫描线、旋转卡壳、半平面交、平面最近点对、随机增量法、反演变换；
其他算法：离散化、双指针、离线算法、分数规划、随机化（随机函数、爬山算法、模拟退火）、悬线法、有限状态自动机、字节顺序、约瑟夫问题、格雷码、表达式求值、在一台机器上的规划任务、主元素问题、Garsia-Wachs算法、15-puzzie、Kahan求和、可多隶属/颜色段均摊、空间优化

""" # 注意：为了简洁，我在这里省略了算法列表，您在实际代码中应保留完整列表

    system_prompt = f"[SYSTEM]\n你是一位世界级的竞赛编程冠军，现在作为人工智能导师，你的目标是用{language}逐步思考并解决给定的编程问题，分析问题。制定策略，编写代码，如果代码出错，分析错误并进行修正\n"
    
    # 将 user_prompt 分为几部分，便于管理
    user_prompt_intro = f"[USER]\n请解决以下编程问题，你的代码应该考虑可能的边界情况，避免编译错误，使用高效的算法使得程序能在1ms内解决问题：\n"
    user_prompt_problem = f"--问题描述--\n{problem_description}\n--问题描述结束--\n"
    user_prompt_guidance = f"""请参考以下知识体系选择你的核心思想：\n{background_knowledge}\n"""

    reflection_prompt = ""
    if submission_history:
        logging.info(f"🔍 检测到 {len(submission_history)} 次历史提交失败，正在构建反思链...")
        reflection_prompt += "\n[SYSTEM]\n你之前的所有尝试都失败了，这是你尝试的历史记录以及评判的反馈，仔细分析他们，找出错误的根本原因，并想出更好的解决办法\n"
        for i, attempt in enumerate(submission_history):
            reflection_prompt += (
                f"\n--- 尝试 #{i + 1} ---\n"
                f"我这次尝试的思路是: {attempt.get('thought', 'N/A')}\n"
                f"提交的代码:\n```{language.lower()}\n{attempt['code']}\n```\n"
                f"评测结果: **{attempt['result_text']}**\n"
                f"错误详情:\n```\n{attempt['error_info']}\n```\n"
            )
        reflection_prompt += (
            "\n[SYSTEM]\n基于对过去所有失败尝试的分析，请提供一个新的思考过程和修正后的代码。"
            "首先，解释你的新思路以及你将要做出的改动，然后提供完整的、修正后的代码。\n"
        )

    final_instruction = """
[USER]
现在，请提供你的解决方案。你的回答必须以一个解释你逻辑的“Thought”部分开始，随后是一个单独的Markdown代码块，其中包含完整的、可运行的代码。
"""
    
    # 构造最终的 Prompt
    full_prompt = system_prompt + user_prompt_intro + user_prompt_problem + user_prompt_guidance + reflection_prompt + final_instruction

    try:
        # --- 关键修复：长度检查和递归逻辑 ---
        # 只有在 submission_history 非空时才检查长度，并且检查的是 full_prompt
        if submission_history and len(full_prompt.encode('utf-8')) > MAX_PROMPT_TOKENS * 3: # 使用字节长度估算，更接近 token
            logging.warning("📜 Prompt过长，将移除最早的失败记录以缩短上下文。")
            # 递归调用时，移除最早的一条历史记录
            return generate_solution_with_llm(problem_details, model_identifier, language, submission_history[1:], attempt_num)

        logging.info("--- 为大语言模型生成的Prompt ---\n" + full_prompt)

        llm = LLM(model_identifier, custom_provider="volcengine")
        response = llm(
            full_prompt,
            structured_output=SolutionOutput.model_json_schema()
        ).result()

        # --- Token 和内容提取 ---
        usage = response.get("usage")
        total_tokens = usage.get("total_tokens", 0) if usage else 0
        
        if total_tokens == 0: # 备用估算
            total_tokens = len(full_prompt.encode('utf-8')) // 2 

        log_message = f"Token用量（来自API）: 总计={total_tokens}" if usage else f"Token用量（估算）: 总计={total_tokens}"
        logging.info(f"--- 来自LLM的完整原始响应 ---\n{json.dumps(response, indent=2, ensure_ascii=False)}")
        logging.info(log_message)

        # --- 结构化输出解析 ---
        structured_data = response.get("structured_output")
        if not isinstance(structured_data, dict) or "code" not in structured_data or not structured_data["code"]:
            logging.error(f"❌ LLM未能返回有效的结构化输出。收到的响应: {structured_data}")
            return None, "LLM未能生成有效代码", total_tokens

        thought = structured_data.get("thought", "")
        code = structured_data.get("code", "")

        logging.info("✅ 大模型已成功生成结构化的代码和思考过程。")
        logging.info(f"Thought Process: {thought}")
        print("-" * 30); print(code); print("-" * 30)

        # --- 保存文件 (这部分逻辑可以保留，用于本地调试) ---
        os.makedirs(SOLUTIONS_DIR, exist_ok=True)
        file_name = f"{PROBLEM_CODE}_attempt_{attempt_num}.md"
        file_path = os.path.join(SOLUTIONS_DIR, file_name)
        lang_tag = "cpp" if language == "C++" else language.lower()
        file_content = f"# {PROBLEM_CODE} 的解决方案 - 尝试 #{attempt_num}\n\n"
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

# def generate_solution_with_llm(problem_details: dict, model_identifier: str, language: str, submission_history: list ,attempt_num:str):
#     """
#     根据问题详情和所有历史失败尝试，构建一个模仿人类思考模式的Prompt，并返回Token使用量。
#     """
#     logging.info("🤖 准备构建Prompt并调用大模型...")
#     # 使用简化题面替代原始题面
#     problem_description = problem_details.get('simplified_description', 
#                                              problem_details['full_markdown_description'])
    
#     system_prompt = f"[SYSTEM]\n你是一位世界级的竞赛编程冠军，现在作为人工智能导师，你的目标是用{language}逐步思考并解决给定的编程问题，分析问题。制定策略，编写代码，如果代码出错，分析错误并进行修正\n"
#     user_prompt = f"""[USER]\n请解决以下编程问题：\n--问题描述--\n{problem_description}\n--问题描述结束--\n：
# 1.  **核心思想**: 选择要使用的主要算法或数据结构，可以从以下方案中选择：

# 基础算法：枚举、模拟、递归&分治、贪心、排序（选择排序、冒泡排序、插入排序、计数排序、基数排序、快速排序、归并排序、堆排序、桶排序、希尔排序、锦标赛排序、Tim排序）、前缀和&差分、二分、倍增、构造；
# 搜索算法：DFS、BFS、双向搜索、启发式搜索、A*、迭代加深搜索、IDA*、回溯法、Dancing Licks、Alpha-Beta剪枝、搜索优化
# 动态规划算法：背包DP、区间DP、DAG上的DP、树形DP、状压DP、数位DP、插头DP、计数DP、动态DP、概率DP、DP套DP、DP优化（单调队列、单调栈优化、，斜率优化、四边形不等式优化、Slope Trick优化、WQS二分、状态设计优化）
# 字符串算法：字符串匹配、字符串哈希、字典树、前缀算法、KMP算法、Boyer-Moore算法、Z函数、AC自动机、后缀数组、后缀自动机、后缀平衡树、广义后缀平衡树、后缀树、Manacher、回文树、序列自动机、最小表示法、Lyndon分解、Main-Lorentz算法
# 数学：进位制、位运算、二进制集合操作、平衡三进制、高精度计算、快速幂、置换和排列、互弧度制与坐标系、复数、数论（素数、最大公约数、数论分块、欧拉函数、筛法、Meissel-Lehmer算法、分解质因数、贝祖定理、类欧几里得算法、欧拉算法&费马小定理、乘法逆元、线性同余方程、中国剩余定理、升幂引理、阶乘取模、卢卡斯定理、同余方程、二次剩余、原根、离散对数、剩余、莫比乌斯反演、杜数筛、Powerful Number筛、Min_25筛、洲阁筛、连分数、Stern-Brocot树与Farey序列、二次城、Pell方程）、多项式与生成函数（代数基本定理、快速傅里叶变换、快速数论变换、快速沃尔什变换、Chirp Z变换、多项式牛顿迭代、多项式多点求值|快速插值、多项式初等函数、常系数齐次线性递推、多项式平移|连续点值平移、符号化方法、Lagrange反演、形似幂级数复合|复合逆、普通生成函数、指数生成函数、狄利克雷生成函数）、组合数学（排列组合、抽屉原理、容斥原理、斐波那契数列、错位排列、卡特兰数、斯特林数、贝尔数、伯努利数、Entringer Number、Eulerian Number、分拆数、范德蒙德卷积、Polya计数、图论计数）、线性代数（向量、内积和外积、矩阵、初等变换、行列式、线性空间、线性基、线性映射、特征多项式、对角化、Jordan标准型）、线性规划（单纯形法）、抽象代数（群论、环论、域论、Schreier-Sims算法）、概率论（条件概率与独立性、随机变量、随机变量的数字特征、概率不等式）、博弈论（公平组合游戏、非公平组合游戏）、数值算法（插值、数值积分、高斯消元、牛顿迭代法）、序理论、杨氏矩阵、拟阵、Beriekamp-Massey算法；
# 数据结构：栈、队列、链表、哈希表、并查集、堆（二叉堆、配对堆、左偏树）、块状数据结构（块状数组、块状链表、树分块、Sqrt Tree）、单调栈、单调队列、ST表、树状数组、线段树（线段树合并&分裂、李超线段树、猫树、区间最值操作&区间历史最值、划分树）、二叉搜索树&平衡树（Treap、Splay树、WBLT、替罪羊树、笛卡尔树、Size Balanced Tree、AVL树、红黑树、左偏红黑树、AA树）、跳表、可持久化数据结构（可持久化线段树、可持久化块状数组、可持久化平衡树、可持久化字典树、可持久化可并堆）、树套树（线段树套线段树、平衡树套线段树、线段树套平衡树、树状数组套权值平衡树、分块套树状数组）、K-D Tree、动态树（Link cut Tree全局平衡二叉树、Euler Tour Tree、Top Tree）、析和树、PQ树、手指树、霍夫曼树；
# 图论：图的存储、DFS、BFS、树上问题（树的直径、树的中心、最近公共祖先、树链剖分、树上启发式合并、虚树、树分治、动态树分治、AHU算法、树哈希、树上随机游走）、有向无环图、拓扑排序、最短路问题（最短路、差分约束、k短路、同余最短路）、生成树问题（最小生成树、最小树形图、最小直径生成树）、斯坦纳树、拆点、连通性相关（强联通分量、双联通分量、割点和桥、圆方图、点/边连通度）环计数问题、最小环、2-SAT、欧拉图、哈密顿图、二分图、平面图、弦图、图的着色、网络流（最大流、最小流、费用流、上下界网络流、Stoer-Wagner算法）、图的匹配（二分图最大匹配、二分图最大权匹配、一般图最大匹配、一般图最大权匹配）、Prufer序列、矩阵树定理、LGV引理、最大团搜索算法、支配树、图上随机游走；
# 计算几何：二维计算几何、三维计算几何、距离、Pick定理、三角剖分、凸包、扫描线、旋转卡壳、半平面交、平面最近点对、随机增量法、反演变换；
# 其他算法：离散化、双指针、离线算法、分数规划、随机化（随机函数、爬山算法、模拟退火）、悬线法、有限状态自动机、字节顺序、约瑟夫问题、格雷码、表达式求值、在一台机器上的规划任务、主元素问题、Garsia-Wachs算法、15-puzzie、Kahan求和、可多隶属/颜色段均摊、空间优化

# 2.  **边界情况**: 需要考虑的潜在边界情况（例如：n=0、空输入、极大/极小的数字、题目约束等）。
# 3.  **时间限制**: 应使用尽可能高效的算法，使得程序能在1000ms内解决问题。
# 4.  **编译错误**: 依据{language}标准给出代码，尽量避免编译错误。\n\n--- 问题描述 ---\n{problem_description}\n--- 问题描述结束 ---\n"""
    
#     reflection_prompt = ""
#     if submission_history:
#         logging.info(f"🔍 检测到 {len(submission_history)} 次历史提交失败，正在构建反思链...")
#         reflection_prompt += "\n[SYSTEM]\n你之前的所有尝试都失败了，这是你尝试的历史记录以及评判的反馈，仔细分析他们，找出错误的根本原因，并想出更好的解决办法\n"
#         for i, attempt in enumerate(submission_history):
#             reflection_prompt += f"\n--- 尝试 #{i + 1} ---\n"
#             reflection_prompt += f"我这次尝试的思路是: {attempt.get('thought', 'N/A')}\n"
#             reflection_prompt += f"提交的代码:\n```{language.lower()}\n{attempt['code']}\n```\n"
#             reflection_prompt += f"评测结果: **{attempt['result_text']}**\n"
#             reflection_prompt += f"错误详情:\n```\n{attempt['error_info']}\n```\n"
#         reflection_prompt += (
#             "\n[SYSTEM]\n基于对过去所有失败尝试的分析，请提供一个新的思考过程和修正后的代码。"
#             "首先，解释你的新思路以及你将要做出的改动，然后提供完整的、修正后的代码。\n"
#         )

#     final_instruction = """
# [USER]
# 现在，请提供你的解决方案。
# """
#     full_prompt = system_prompt + user_prompt + reflection_prompt + final_instruction
#     try:
#         if len(full_prompt) > MAX_PROMPT_TOKENS * 0.9:
#             logging.warning("📜 Prompt过长，将移除最早的失败记录。")
#             return generate_solution_with_llm(problem_details, model_identifier, language, submission_history[1:],
#                                               attempt_num)

#         logging.info("--- 为大语言模型生成的Prompt ---\n" + full_prompt)

#         llm = LLM(model_identifier)

#         # --- 2. 使用结构化输出调用 LLM ---
#         response = llm(
#             full_prompt,
#             structured_output=SolutionOutput.model_json_schema()
#         ).result()

#         # --- 3. 精确提取Token和内容 ---
#         usage = response.get("usage", {})
#         total_tokens = usage.get("total_tokens", 0)

#         if total_tokens == 0:
#             # 估算逻辑作为备用
#             content_for_estimation = json.dumps(response.get("structured_output", {}))
#             total_tokens = estimate_tokens(full_prompt) + estimate_tokens(content_for_estimation)
#             log_message = f"Token用量（估算）: 总计={total_tokens}"
#         else:
#             log_message = f"Token用量（来自API）: 总计={usage.get('total_tokens')}"

#         logging.info(f"--- 来自LLM的完整原始响应 ---\n{json.dumps(response, indent=2, ensure_ascii=False)}")
#         logging.info(log_message)

#         # --- 4. 直接从结构化输出中获取数据，不再需要解析 ---
#         structured_data = response.get("structured_output")
#         if not isinstance(structured_data, dict):
#             logging.error(f"❌ LLM未能返回有效的结构化输出。收到的响应: {structured_data}")
#             return None, None, total_tokens

#         thought = structured_data.get("thought", "")
#         code = structured_data.get("code", "")

#         if not code:
#             logging.error("❌ 结构化输出中未能找到代码。")
#             return None, thought, total_tokens

#         logging.info("✅ 大模型已成功生成结构化的代码和思考过程。")
#         logging.info(f"Thought Process: {thought}")
#         print("-" * 30);
#         print(code);
#         print("-" * 30)

#         # --- 5. 保存文件 (逻辑保持不变) ---
#         os.makedirs(SOLUTIONS_DIR, exist_ok=True)
#         file_name = f"{PROBLEM_CODE}_attempt_{attempt_num}.md"
#         file_path = os.path.join(SOLUTIONS_DIR, file_name)
#         lang_tag = "cpp" if language == "C++" else language.lower()
#         file_content = f"# {PROBLEM_CODE} 的解决方案 - 尝试 #{attempt_num}\n\n"
#         if submission_history:
#             file_content += "## 关于过去失败的反思\n\n此代码是基于先前错误修正后的版本。\n\n"
#         file_content += f"## 思考过程\n\n{thought}\n\n"
#         file_content += f"## 生成的代码 ({language})\n\n```{lang_tag}\n{code}\n```\n```\n"
#         with open(file_path, 'w', encoding='utf-8') as f:
#             f.write(file_content)
#         logging.info(f"💾 解决方案已成功保存到: {file_path}")

#         return code, thought, total_tokens

#     except Exception as e:
#         logging.critical(f"❌ 调用或解析LLM时发生严重错误: {e}")
#         logging.critical(traceback.format_exc())
#         return None, None, 0

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
    test_cases = generate_edge_cases_with_llm(problem_details, llm_model)[:DUIPAI_COUNT]
    
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

#处理学生提交的代码
def process_student_solution(problem_id: str, student_code: str, problem_desc: str, session: requests.Session, submission_history: list):
    """
    【最终修正版】处理学生提交的错误代码，并确保向 submission_history 添加的记录结构统一。
    """
    logging.info(f"--- 正在处理学生解法，题目 ID: {problem_id} ---")
    
    # 1. 提取解法描述
    solution_info = extract_solution_from_code(student_code, problem_desc, LLM_MODEL_FOR_ANALYSIS)
    if not solution_info or 'description' not in solution_info or solution_info['description'] == "解法提取失败":
        logging.error("❌ 无法提取解法描述，将使用通用描述。")
        solution_desc = "学生提供了一段代码，但未能自动提取其核心思路。"
    else:
        solution_desc = solution_info['description']
    logging.info(f"📝 提取的解法描述: {solution_desc}")

    # 2. LLM 判断错误类型
    error_analysis = judge_error_type_with_llm(problem_desc, student_code, LLM_MODEL_FOR_ANALYSIS)
    
    # 3. 根据错误类型进行分支处理
    if error_analysis["error_type"] == "conceptual":
        logging.info("💡 判定为概念性错误。")
        counter_example_info = generate_counter_example_with_llm(
            problem_desc, student_code, error_analysis, LLM_MODEL_FOR_ANALYSIS
        )
        
        # 统一添加记录
        submission_history.append({
            "code": student_code,
            "thought": f"学生代码分析 - 概念性错误: {error_analysis.get('reasoning', 'N/A')}",
            "result_text": "Conceptual Error (Analyzed)",
            "error_info": error_analysis.get("reasoning", "N/A")
        })
        
        return {
            "status": "conceptual_error", 
            "message": f"识别到概念性错误: {error_analysis['reasoning']}",
            "analysis": error_analysis,
            "counter_example": counter_example_info
        }

    elif error_analysis["error_type"] == "implementation":
        logging.info("💡 判定为实现性错误。")
        
        # 向量化并搜索相似错误 (这部分逻辑不变)
        embedding_future = Embedding()(solution_desc)
        embedding = embedding_future.result()
        if embedding:
            similar_errors = knowledge_base.search_similar_errors(problem_id, embedding)
            if similar_errors:
                logging.info(f"✅ 在知识库中找到相似的实现性错误。")
                # (此处可以添加返回已有分析的逻辑)
        
        # 无论是否找到，都继续进行详细分析并添加新记录
        logging.info("🆕 正在使用 LLM 详细分析实现性错误...")
        implementation_analysis = analyze_implementation_error_with_llm(
            problem_desc, student_code, error_analysis, LLM_MODEL_FOR_ANALYSIS
        )
        
        # 添加到知识库
        error_id = knowledge_base.add_error_sample(problem_id, solution_desc, student_code)
        
        # 统一添加记录
        submission_history.append({
            "code": student_code,
            "thought": f"学生代码分析 - 实现性错误: {implementation_analysis.get('implementation_analysis', 'N/A')}",
            "result_text": "Implementation Error (Analyzed)",
            "error_info": json.dumps(implementation_analysis, ensure_ascii=False, indent=2)
        })
        
        return {
            "status": "implementation_error", 
            "message": f"识别到实现性错误",
            "analysis": implementation_analysis,
            "error_id": error_id
        }
            
    else: # 未知错误类型
        logging.warning("❓ LLM 未能明确分类错误类型。")
        
        # 统一添加记录
        submission_history.append({
            "code": student_code,
            "thought": "学生代码分析 - 未知错误类型",
            "result_text": "Unknown Error Type (Analyzed)",
            "error_info": error_analysis.get("reasoning", "N/A")
        })

        return {
            "status": "unknown_error", 
            "message": f"LLM未能明确分类错误类型。分析: {error_analysis['reasoning']}",
            "analysis": error_analysis
        }



#--- 主执行流程 __main__  ---
def main():
    global session
    """主执行函数，封装所有流程"""
    username = os.getenv("SDUOJ_USERNAME", "202300130111")
    password = os.getenv("SDUOJ_PASSWORD", "1517287203Syx")

    if username == "202300130111":
        logging.info(f"使用默认用户名: {username}")
    else:
        username = input("请输入您的 SDUOJ 用户名: ")
        password = getpass.getpass("请输入您的 SDUOJ 密码: ")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'{BASE_URL}/v2/problem/{PROBLEM_CODE}',
    })

    logging.info("-" * 50)
    logging.info(f"准备开始自动化流程，目标题目: {PROBLEM_CODE}")
    logging.info("-" * 50)
    student_code = """
#include <iostream>
#include <cmath>
using namespace std;

// 错误的阶乘计算（本应计算 (N-1)!，但错误计算 N! ）
long long factorial(int n) {
    long long res = 1;
    for (int i = 1; i <= n; ++i) {
        res *= i;
    }
    return res;
}

int main() {
    int T;
    cin >> T;
    while (T--) {
        int N;
        cin >> N;
        
        // 错误逻辑：概率 = 1 / N!
        long long fact = factorial(N);
        double prob = 1.0 / fact;
        
        // 输出结果（错误）
        printf("%.10lf\n", prob);
    }
    return 0;
}
"""
    with Context(router="1234567890", task_id=f"sduoj-agent-{str(uuid.uuid4())[:8]}"):
        global knowledge_base
        knowledge_base = KnowledgeBase()
        if not login(session, username, password): return
        
        problem_details = get_problem_details(session, PROBLEM_CODE)
        if not problem_details: return

        # === 阶段一: 题目深度分析 (为知识库“备课”) ===
        logging.info("\n" + "="*20 + " 阶段一: 题目深度分析 " + "="*20)
        
        simplified_content = generate_problem_simplified(
            problem_details['full_markdown_description'], LLM_MODEL_FOR_ANALYSIS
        )
        knowledge_base.save_problem_simplified(PROBLEM_CODE, simplified_content)
        problem_details['simplified_description'] = simplified_content
        logging.info("📊 简化题面已生成并存入知识库。")

        errors_md = generate_possible_errors(
            problem_details['full_markdown_description'], LLM_MODEL_FOR_ANALYSIS
        )
        knowledge_base._upload(f"{PROBLEM_CODE}/possible_errors.md", errors_md)
        logging.info("📋 潜在错误分析已生成并存入知识库。")
        
        edge_md = generate_edge_cases_with_llm(
            problem_details['full_markdown_description'], LLM_MODEL_FOR_ANALYSIS
        )
        knowledge_base._upload(f"{PROBLEM_CODE}/edge_cases.md", edge_md)
        logging.info("🧪 边缘测试用例分析已生成并存入知识库。")

        # === 阶段二: 学生代码分析与自主解题 ===
        logging.info("\n" + "="*20 + " 阶段二: 代码分析与自主解题 " + "="*20)
        
        submission_history = []
        
        # --- 2a. (可选) 分析一个初始的错误代码，作为学习起点 ---
        logging.info("\n--- 首先分析一个已知的错误学生代码 ---")
        analysis_result = process_student_solution(
            problem_id=PROBLEM_CODE,
            student_code=student_code,
            problem_desc=problem_details['full_markdown_description'],
            session=session,
            submission_history=submission_history  # 传递 history 列表以记录分析结果
        )
        logging.info(f"学生代码分析完成，状态: {analysis_result.get('status')}")
        
        # --- 2b. AI 基于分析结果（或从零开始）自主解题 ---
        logging.info("\n--- AI 开始自主解题（可能已从学生错误中学习）---")
        total_tokens_used = 0
        solution_accepted = False
        
        while len(submission_history) < MAX_ATTEMPTS:
            attempt_num = len(submission_history) + 1
            logging.info(f"🚀 开始第 {attempt_num}/{MAX_ATTEMPTS} 次常规提交尝试...")

            solution_code, thought, tokens_this_call = generate_solution_with_llm(
                problem_details, LLM_MODEL_FOR_ANALYSIS,
                SUBMISSION_LANGUAGE, submission_history, attempt_num
            )
            total_tokens_used += tokens_this_call

            if not solution_code:
                logging.error("🧠 LLM未能生成有效代码，终止尝试。")
                break
            
            # 自动提交
            submission_id = submit_solution(session, problem_details['id'], solution_code, SUBMISSION_LANGUAGE)
            if not submission_id:
                submission_history.append({"code": solution_code, "thought": thought, "result_text": "Submission API Failed", "error_info": "API call failed."})
                continue
            
            result_data = check_submission_status(session, submission_id)
            if result_data:
                status_code = result_data.get("judgeResult")
                if status_code == 1:
                    logging.info("🏆🎉 恭喜！问题已解决！")
                    solution_accepted = True
                    knowledge_base.add_solution(
                        problem_id=PROBLEM_CODE,
                        desc=f"第 {attempt_num} 次尝试成功通过的 AI 解法: {thought}",
                        code=solution_code
                    )
                    break
                
                status_text = JUDGE_STATUS.get(status_code, f"Unknown Status ({status_code})")
                logging.warning(f"😔 本次尝试未通过，结果: {status_text}。")
                error_info = result_data.get("judgeInfo", "No specific error info.")
                submission_history.append({"code": solution_code, "thought": thought, "result_text": status_text, "error_info": error_info})
            else:
                logging.error("无法获取评测结果，终止尝试。")
                break
        
        # --- 2c. 失败后进入对拍模式 ---
        if not solution_accepted and submission_history and submission_history[-1]['code']:
            last_failed_code = submission_history[-1]['code']
            pairwise_testing_mode(
                problem_details,
                last_failed_code,
                LLM_MODEL_FOR_ANALYSIS,
                SUBMISSION_LANGUAGE
            )
        elif solution_accepted:
            logging.info("代码已通过OJ评测，流程结束。")
        else:
            logging.warning("所有尝试均失败，且无法进入对拍模式。")
#清空milvus
# def main():
#     with Context(router = "123",task_id = "clean milvus"):
#         vdb=VectorDB()
#         vdb("drop_collection", collection_name="problem_embeddings").result() 
#         vdb("drop_collection", collection_name="problem_errors").result() 

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