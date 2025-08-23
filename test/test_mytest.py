import os #处理文件路径
import uuid
from core.Context import Context
from coper.LLM import LLM


def generic_code_check(code_path: str, model_name: str) -> str:
    """
    对给定的代码文件进行通用性分析，指出错误和优化点。
    """
    print(f"--- Running Generic Code Check on: {code_path} ---")
    print(f"--- Using Model: {model_name} ---")

    #检查并读取文件
    if not os.path.exists(code_path):
        error_msg = f"Error: File not found at '{code_path}'."
        print(error_msg)
        return error_msg

    try:
        with open(code_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        error_msg = f"Error: Could not read file at '{code_path}'. Reason: {e}"
        print(error_msg)
        return error_msg

    #初始化LLM
    try:
        llm = LLM(model_name)
    except Exception as e:
        error_msg = f"Error: Failed to initialize LLM with model '{model_name}'. Reason: {e}."
        print(error_msg)
        return error_msg

    #先定义好要使用的prompt

    prompt = f"""
    You are a world-class C++ software engineer and an expert in competitive programming, specializing in code reviews.
    Your task is to provide a thorough review of the following C++ code.

    Please structure your feedback into two distinct, clearly labeled sections using Markdown:
    1.  **Potential Bugs & Critical Errors:** Identify and explain any potential bugs, logical fallacies, undefined behavior, memory issues (like leaks or corruption), or security vulnerabilities. For each point, explain the potential consequence.
    2.  **Optimization & Readability Suggestions:** Provide actionable advice to improve the code. This includes performance optimizations, style improvements, modern C++ best practices (e.g., C++11/17/20 features), and ways to make the code more readable and maintainable.

    Ensure your analysis is constructive, clear, and provides specific examples where possible.

    ---
    **C++ Code for Review:**
    ```cpp
    {code_content}
    ```"""

    #使用定义好的prompt调用LLM 
    try:
        response = llm(prompt).result()
        analysis_report = response.get("content", "Analysis failed: No content was returned from the LLM.")
    except Exception as e:
        analysis_report = f"An error occurred while communicating with the LLM: {e}. Check your network connection and API credentials."
        print(analysis_report) #出错时也打印信息

    #在函数的最后，返回最终结果
    return analysis_report

if __name__ == "__main__":
    with Context(task_id=str(uuid.uuid4().hex)):

        #定义要检查的 C++ 代码文件路径。
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cpp_file_to_check = os.path.join(script_dir, "sample_code.cpp")
    
        #定义要使用的 LLM 模型
        llm_model_for_analysis = "volcengine/doubao-1-5-thinking-pro-250415"

        #调用上面定义的函数，传入配置好的参数
        analysis_result = generic_code_check(
            code_path=cpp_file_to_check,
            model_name=llm_model_for_analysis
        )
    
        #打印从函数返回的详细分析报告
        print("\n" + "="*25 + " ANALYSIS REPORT " + "="*25)
        print(analysis_result)
        print("="*70 + "\n")
        print("Script execution finished successfully.")