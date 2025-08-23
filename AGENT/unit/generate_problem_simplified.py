import uuid
import re
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import traceback
import logging
from AGENT.unit.pydantic_models import SimplifiedProblemOutput
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
def generate_problem_simplified(problem_content: str, model_identifier: str) -> str:
    """
    生成简化的数学形式题目描述 (problem_s.md)
    """
    logging.info("📝 开始生成简化数学形式的题目描述...")
    
    base_prompt = f"""
【角色】
你是一名“极简题面生成器”，只输出数学形式，不讲故事。

【输入】
{problem_content}

【任务】
生成一份“纯技术规格”文档，要求：
1. 删除所有背景、故事、情境、示例解释、提示。
2. 用符号表达：输入集合、输出集合、约束条件、数学关系。
3. 必须包含：变量名及类型、变量上下界、运算/逻辑关系式。
4. 禁止出现任何自然语言描述、样例或解释性文字。
"""

    # --- 1. 结构化输出的 Prompt ---
    structured_prompt = base_prompt + """
【输出要求】
你的输出必须是一个只包含 `simplified_description` 键的 JSON 对象，其值为符合上述任务要求的 Markdown 格式字符串。
"""

    # --- 2. 自然语言输出的 Prompt ---
    natural_prompt = base_prompt + """
【输出模板】（严格按 Markdown 层级）
```markdown
## 问题定义

### 输入
- 变量：`a`, `b`
- 类型：整数
- 范围：`1 ≤ a, b ≤ 10^9`

### 输出
- 变量：`s`
- 类型：整数

### 关系
- `s = a + b`
请仅填充模板，不要添加额外文字。
"""

    try:
        # 核心修改：使用传入的参数
        llm = LLM(model=model_identifier)
        simplified_content = None

        # === 主模式：尝试结构化输出 ===
        try:
            response = llm(prompt=structured_prompt, structured_output=SimplifiedProblemOutput.model_json_schema()).result()
            structured_data = response.get("structured_output")
            
            if structured_data and "simplified_description" in structured_data:
                simplified_content = structured_data.get("simplified_description")
                logging.info("✅ 已通过结构化输出生成简化题面。")
        
        except Exception as e:
            logging.warning(f"结构化输出失败: {e}, 将尝试自然语言解析方式...")

        # === 备用模式：如果主模式失败，则获取自然语言输出 ===
        if not simplified_content:
            response = llm(prompt=natural_prompt).result()
            content = response.get("content", "")
            # 尝试从 Markdown 代码块中提取内容
            match = re.search(r"```markdown\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                simplified_content = match.group(1).strip()
            else:
                simplified_content = content.strip()
            
            if simplified_content:
                logging.info("✅ 已通过自然语言格式生成简化题面。")
        
        # --- 构建并返回最终结果 ---
        if not simplified_content:
            logging.error("❌ 两种方式均未能生成有效的简化题面，将返回原始题面。")
            return problem_content

        # 确保返回的内容是一个完整的 Markdown 文档
        if not simplified_content.strip().startswith("##"):
            simplified_content = f"## 问题定义\n\n{simplified_content}"
        
        logging.info("✅ 简化题面生成成功！")
        return simplified_content

    except Exception as e:
        logging.error(f"❌ 生成简化题面时发生严重错误: {e}")
        logging.error(traceback.format_exc())
        return problem_content  # 失败时返回原始题面