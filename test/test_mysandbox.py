# file: clean_output_diagnoser.py

import os
import shutil
import tempfile
import uuid
import logging
from datetime import datetime

# 导入必要的模块
from coper.Minio import Minio
from coper.Service import Service
from coper.LLM import LLM
from core.Context import Context
from core.Utils import zip_directory_to_bytes, unzip_bytes_to_directory

# --- 1. 配置日志记录 (只写入文件) ---
# 创建一个唯一的日志文件名
log_filename = f"diagnoser_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 配置日志记录器，只将日志输出到文件，不在终端显示
logging.basicConfig(
    level=logging.INFO, # 记录INFO级别及以上的信息
    format='%(asctime)s [%(levelname)-8s] in %(funcName)s: %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8')
    ]
)

# --- 2. 测试用例 ---
TEST_CASES = [
    # --- 原始测试用例 ---
    {
        "name": "Python - 运行时错误 (除零)",
        "language": "python",
        "filename": "div_by_zero.py",
        "code": "a = 10\nb = 0\nprint(a / b)",
    },
    {
        "name": "C++ - 编译错误 (缺少分号)",
        "language": "cpp",
        "filename": "missing_semicolon.cpp",
        "code": "#include <iostream>\nint main() { std::cout << 1\nreturn 0; }",
    },
    {
        "name": "Python - 超时错误 (无限循环)",
        "language": "python",
        "filename": "time_limit.py",
        "code": "while True:\n  pass",
    },
    {
        "name": "Python - 正常运行 (用于对比)",
        "language": "python",
        "filename": "success.py",
        "code": "print(10 + 20)",
        "expected_output": "30"
    },
    # --- [新增] 更多测试用例 ---
    {
        "name": "C++ - 运行时错误 (段错误)",
        "language": "cpp",
        "filename": "segfault.cpp",
        "code": "#include <iostream>\nint main() { int* ptr = nullptr; *ptr = 42; return 0; }",
    },
    {
        "name": "C++ - 链接错误 (未定义引用)",
        "language": "cpp",
        "filename": "linker_error.cpp",
        "code": "#include <iostream>\nvoid undefined_function();\nint main() { undefined_function(); return 0; }",
    },
    {
        "name": "Python - 运行时错误 (NameError)",
        "language": "python",
        "filename": "name_error.py",
        "code": "a = 10\nprint(a + b)", # 'b' is not defined
    },
    {
        "name": "Python - 运行时错误 (IndexError)",
        "language": "python",
        "filename": "index_error.py",
        "code": "my_list = [10, 20, 30]\nprint(my_list[3])", # Index 3 is out of bounds
    },
    {
        "name": "Python - 逻辑错误 (Wrong Answer)",
        "language": "python",
        "filename": "wrong_answer.py",
        "code": "print(10 * 2 - 5)", # Code runs, but logic might be wrong for a given problem
        "expected_output": "15" # The system will report this as success
    },
    {
        "name": "C++ - 主动失败 (非零退出码)",
        "language": "cpp",
        "filename": "non_zero_exit.cpp",
        "code": "#include <iostream>\nint main() { std::cerr << \"Controlled failure.\"; return 1; }",
    },
]


# --- 3. 核心功能函数 (内部使用 logging 记录详细步骤) ---

def execute_in_sandbox(case_name: str, source_code: str, language: str, filename: str, timeout: int = 5):
    """
    在沙箱中执行代码并返回详细结果。此函数在后台记录详细日志。
    """
    # (此函数逻辑与之前版本类似，但所有print都换成了logging.info)
    lang_to_template = {"python": "python-3.12", "cpp": "gcc-13.3-cpp-std_17-O2"}
    lang_to_target_filename = {"python": "main.py", "cpp": "main.cc"}
    
    target_filename = lang_to_target_filename[language]
    base_dir = tempfile.mkdtemp()
    bucket_name = f"sandbox-run-{uuid.uuid4().hex}"
    io = Minio()
    
    try:
        logging.info(f"[{case_name}] Preparing local files...")
        source_dir = os.path.join(base_dir, "source")
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(source_dir); os.makedirs(data_dir)
        with open(os.path.join(source_dir, target_filename), "w", encoding="utf8") as f: f.write(source_code)
        with open(os.path.join(data_dir, "input"), "w", encoding="utf8") as f: f.write("\n") # 确保输入非空
        
        source_zip_bytes = zip_directory_to_bytes(source_dir)
        data_zip_bytes = zip_directory_to_bytes(data_dir)
        
        logging.info(f"[{case_name}] Uploading to MinIO bucket '{bucket_name}'...")
        io("make_bucket", bucket_name).result()
        source_file_ref = io("write", bucket_name, "source.zip", source_zip_bytes)
        data_file_ref = io("write", bucket_name, "data.zip", data_zip_bytes)
        output_file_ref = {"bucket": bucket_name, "object_name": "output.zip"}

        logging.info(f"[{case_name}] Calling code-sandbox service...")
        code_sandbox = Service("code-sandbox")
        exec_result = code_sandbox(
            source_file=source_file_ref, data_file=data_file_ref, command_file=None,
            output_file=output_file_ref, execution_timeout=timeout, execution_memory=256,
            sandbox_template=lang_to_template[language]
        ).result()
        logging.info(f"[{case_name}] Raw sandbox response: {exec_result}")

        stdout_content = ""
        output_zip_bytes = io("read", bucket_name, "output.zip").result()
        if output_zip_bytes:
            output_dir = os.path.join(base_dir, "output")
            os.makedirs(output_dir)
            unzip_bytes_to_directory(output_zip_bytes, output_dir)
            output_file_path = os.path.join(output_dir, "output")
            if os.path.exists(output_file_path):
                with open(output_file_path, "r", encoding="utf8") as f:
                    stdout_content = f.read()

        # 解析并返回结构化结果
        final_result = { "stdout": stdout_content.strip(), "filename": filename, "original_filename": filename }
        if 'error' in exec_result and exec_result['error']:
            status = exec_result['error']
            if "TIME_LIMIT_EXCEEDED" in status: status = "TimeLimitExceeded"
            elif status == "COMPILATION_ERROR": status = "CompilationError"
            elif status == "RUNTIME_ERROR": status = "RuntimeError"

            final_result['status'] = status
            final_result['exit_code'] = 1
            if status == 'CompilationError':
                final_result['stderr'] = exec_result.get('compilation', {}).get('log', exec_result.get('error_msg', ''))
            else:
                final_result['stderr'] = exec_result.get('stderr', exec_result.get('error_msg', ''))
        else:
            final_result['status'] = "Success"
            final_result['exit_code'] = exec_result.get('running', {}).get('exit_code', 0)
            final_result['stderr'] = exec_result.get('running', {}).get('stderr', '')
        
        # 增加一个检查：即使沙箱没有报告顶层 'error'，如果 exit_code 不为 0，也应标记为 RuntimeError
        if final_result['status'] == 'Success' and final_result['exit_code'] != 0:
            final_result['status'] = 'RuntimeError'
            
        return final_result

    finally:
        logging.info(f"[{case_name}] Cleaning up resources...")
        try:
            io("delete_bucket", bucket_name).result()
        except Exception as e:
            logging.warning(f"[{case_name}] Failed to delete bucket '{bucket_name}'. Reason: {e}")
        shutil.rmtree(base_dir)

def get_llm_diagnosis(model_name: str, code: str, language: str, sandbox_error: dict) -> str:
    """
    当代码执行失败时，调用LLM进行分析。
    """
    logging.info(f"Engaging LLM '{model_name}' for case '{sandbox_error.get('original_filename')}'.")
    # (此处的 Prompt 与之前版本完全相同，保持高度结构化)
    prompt = f"""
You are an expert code diagnostician. A piece of {language} code failed to execute in a secure sandbox environment. 
Your task is to analyze the source code and the sandbox error log to provide a clear, concise, and actionable diagnosis.

**Provided Information:**

1.  **Source Code (`{sandbox_error.get('original_filename', 'source')}`):**
    ``` {language}
    {code}
    ```

2.  **Sandbox Execution Log:**
    ```
    Status: {sandbox_error.get('status', 'N/A')}
    Exit Code: {sandbox_error.get('exit_code', 'N/A')}
    Stderr:
    {sandbox_error.get('stderr', 'N/A')}
    ```

**Required Output Format:**

Please structure your response using the following Markdown format. Be precise and focus only on the root cause.

### 1. 错误诊断 (Error Diagnosis)
*   **错误类型**: [例如：运行时错误 (Runtime Error), 编译错误 (Compilation Error), 超时错误 (Time Limit Exceeded)]
*   **根本原因**: [用一句话简明扼要地解释为什么会发生这个错误。]

### 2. 错误定位 (Error Location)
*   **文件名**: `{sandbox_error.get('original_filename', 'source')}`
*   **行号**: [指出错误发生的具体行号]
*   **错误代码**: 
    ``` {language}
    [这里只粘贴导致错误的那一行代码]
    ```

### 3. 修改建议 (Modification Suggestion)
*   **说明**: [简要说明修改思路。]
*   **修正后代码**:
    ``` {language}
    [提供可以直接替换的、修正后的代码片段。]
    ```
"""
    try:
        llm = LLM(model_name)
        response = llm(prompt).result()
        return response.get("content", "Analysis failed: No content returned from the LLM.")
    except Exception as e:
        logging.error(f"LLM analysis failed due to an exception: {e}", exc_info=True)
        return f"LLM analysis failed due to an exception: {e}"

# --- 4. 主调度函数 (负责在终端打印美化输出) ---
def run_and_diagnose_with_llm(model_name: str, case: dict):
    """
    执行代码。如果成功，则安静通过；如果失败，则在终端打印LLM的诊断报告。
    """
    case_name = case['name']
    
    # 在终端打印每个案例的标题
    print(f"\n{'='*25} RUNNING CASE: {case_name} {'='*25}")
    
    try:
        # 1. 在沙箱中执行代码
        sandbox_result = execute_in_sandbox(
            case_name=case_name,
            source_code=case["code"],
            language=case["language"],
            filename=case["filename"],
            timeout=2
        )

        # 2. 检查执行结果
        if sandbox_result.get('status') == 'Success' and sandbox_result.get('exit_code') == 0:
            # 如果成功，只在终端打印一个简单的成功信息
            print(f"✅ Execution Successful. Output: '{sandbox_result['stdout']}'")
        else:
            # 3. 如果失败， engaging LLM 并打印报告
            print("\n>>> Code execution failed. Engaging LLM for analysis...")
            llm_report = get_llm_diagnosis(
                model_name=model_name,
                code=case["code"],
                language=case["language"],
                sandbox_error=sandbox_result
            )
            print("\n--- LLM-Powered Diagnosis Report ---")
            print(llm_report)

    except Exception as e:
        # 如果测试执行器本身崩溃，也在终端打印严重错误
        print(f"\n🔥 CRITICAL ERROR: The test runner itself crashed for case '{case_name}'.")
        print(f"   Please check the log file '{log_filename}' for the full traceback.")
        logging.critical(f"Test runner crashed for case '{case_name}'", exc_info=True)
    
    finally:
        # 在终端打印每个案例的结束符
        print(f"\n{'='*30} CASE FINISHED {'='*30}\n")


if __name__ == "__main__":
    with Context(task_id=str(uuid.uuid4().hex)):
        # 定义要使用的 LLM 模型
        llm_model_for_analysis = "volcengine/doubao-1-5-thinking-pro-250415"

        for test_case in TEST_CASES:
            run_and_diagnose_with_llm(
                model_name=llm_model_for_analysis,
                case=test_case
            )
        
        # 在所有测试结束后，在终端打印总结
        print(f"\n✅ All tests finished. A detailed execution log has been saved to '{log_filename}'.\n")