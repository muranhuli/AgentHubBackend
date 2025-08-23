
import re
import logging
from coper.LLM import LLM
from core.Context import Context
import traceback
from AGENT.unit.pydantic_models import GeneralCodeCheckOutput
# 初始化日志
log_filename = "general_code_check.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
SOURE_LANGUAGE = "C++14"
def general_code_check(student_code: str, llm_model: str) -> str:
    """
    使用 LLM 对给定的源代码进行通用型检查。
    优先尝试结构化输出，失败则回退到自然语言解析。
    返回一个格式化的 Markdown 报告字符串。
    """
    logging.info("🤖 LLM: 正在执行通用型代码检查...")

    base_prompt = f"""
[SYSTEM]
你是一位资深代码审计专家。请对以下 {SOURE_LANGUAGE} 代码进行通用型检查，并按照以下要求输出报告：

### 一、审查维度（必须覆盖所有子项）
1. **语法与编译问题**：检查语法错误、未定义行为（如未初始化变量、整数溢出、越界访问）、不符合 C++ 标准的写法（如 C 风格强制转换 vs static_cast）。
2. **逻辑与正确性**：检查循环条件（如边界值是否闭合）、条件判断（如是否遗漏等价情况）、算法逻辑（如计算逻辑是否与需求一致）。
3. **性能与效率**：检查不必要的拷贝（如传值而非传 const 引用）、循环内的冗余操作（如重复计算相同表达式）、资源管理（如文件/内存未及时释放）。
4. **安全性**：检查不安全的输入处理（如未校验 cin 输入有效性）、潜在的内存泄漏（如 new 后未 delete）、危险的函数调用（如 gets()、strcpy() 等已被弃用的函数）。
5. **代码可读性与风格**：检查命名规范（变量/函数名是否符合驼峰式或下划线式）、注释质量（关键逻辑是否有注释）、代码缩进与格式（是否符合 Google C++ 风格指南）。
6. **最佳实践**：检查是否使用现代 C++ 特性（如 auto、范围 for 循环替代传统循环）、是否避免全局变量/using namespace std;、是否合理使用 const 修饰符。

[待检查代码]
{SOURE_LANGUAGE.lower()}
{student_code}
"""
    structured_prompt = base_prompt + """
error_check_report: Markdown 格式的字符串，列出所有发现的代码错误问题。如果没有，请填写 "未发现代码错误"。
optimization_suggestions: Markdown 格式的字符串，列出所有代码优化建议。如果没有，请填写 "无优化建议"。
""" 
    natural_prompt = base_prompt + """
[任务]
请以清晰的 Markdown 格式输出你的审查报告，必须包含以下两个二级标题：
代码错误检查
<在这里列出所有错误问题>
优化建议
<在这里列出所有优化建议>
如果代码没有发现任何问题，请在对应标题下明确说明。
"""
    try:
        llm = LLM(model=llm_model)
        report_content = None

        # === 主模式：尝试结构化输出 ===
        try:
            response = llm(structured_prompt, structured_output=GeneralCodeCheckOutput.model_json_schema()).result()
            structured_data = response.get("structured_output")

            if structured_data and "error_check_report" in structured_data and "optimization_suggestions" in structured_data:
                errors = structured_data.get("error_check_report")
                suggestions = structured_data.get("optimization_suggestions")
                # 将结构化结果格式化为最终的报告
                report_content = f"## 代码错误检查\n{errors}\n\n## 优化建议\n{suggestions}"
                logging.info("✅ AI 已通过结构化输出生成代码检查报告。")
        
        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 将尝试自然语言解析方式...")

        # === 备用模式：如果主模式失败，则直接获取自然语言输出 ===
        if not report_content:
            response = llm(natural_prompt).result()
            content = response.get("content", "")
            logging.debug(f"LLM 通用检查（自然语言）结果:\n{content}")
            report_content = content.strip() # 直接使用模型的 Markdown 输出
            if report_content:
                logging.info("✅ AI 已通过自然语言格式生成代码检查报告。")

        # --- 构建并返回最终报告 ---
        if not report_content:
            report_content = "LLM 未能生成有效的检查报告。"

        final_report = "【通用代码检查报告】\n\n" + report_content
        return final_report

    except Exception as e:
        logging.error(f"❌ 通用代码检查时发生严重错误: {e}")
        logging.error(traceback.format_exc())
        return f"【通用代码检查报告】\n\nLLM 在执行检查时发生异常: {e}"
        