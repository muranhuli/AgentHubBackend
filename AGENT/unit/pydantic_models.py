# pydantic_models.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any

class TestCase(BaseModel):
    """测试用例数据结构"""
    input_data: Any = Field(..., description="测试用例的输入数据 (可以是字符串、字典等)。")
    expected_output: Any = Field(..., description="对应输入的预期正确输出 (可以是字符串、列表等)。")
    description: str = Field(..., description="简要说明该测试用例旨在检查的边界或特定情况。")
    case_type: str = Field(..., description="用例类型，必须是 'basic' (基础), 'boundary' (边界), 或 'edge' (边缘) 之一。")

class TestCaseList(BaseModel):
    """用于包裹测试用例列表的 Pydantic 模型"""
    test_cases: List[TestCase] = Field(..., description="一个包含多个测试用例对象的列表。")

class SolutionOutput(BaseModel):
    """用于代码生成和修复的 Pydantic 模型"""
    thought: str = Field(..., description="一步步解释代码背后逻辑的思考过程。")
    code: str = Field(..., description="用于解决问题的完整、可运行的源代码。")

class ErrorTypeAnalysisOutput(BaseModel):
    """用于错误类型分析的 Pydantic 模型"""
    error_type: str = Field(..., description="错误的类型，必须是 'conceptual' (概念性), 'implementation' (实现性), 或 'unknown' (未知) 之一。")
    reasoning: str = Field(..., description="对该分类的详细解释说明。")

class CounterExampleOutput(BaseModel):
    """用于生成反例的 Pydantic 模型"""
    input_data: str = Field(..., description="一个能够暴露概念性错误的具体输入。")
    expected_output: str = Field(..., description="为所生成的输入提供的正确输出。")

class ImplementationAnalysisOutput(BaseModel):
    """用于实现性错误分析的 Pydantic 模型"""
    analysis: str = Field(..., description="对代码中具体实现错误的详细分析，指出错误的代码行或代码段，并解释其错误原因。")
    suggestion: str = Field(..., description="提供具体的、可操作的修复建议，可以是一个修正后的代码片段或清晰的修复说明。")

class SimplifiedProblemOutput(BaseModel):
    """用于简化题面的 Pydantic 模型"""
    simplified_description: str = Field(..., description="以纯技术或数学 Markdown 格式表示的简化版题目描述。")

class PossibleErrorsOutput(BaseModel):
    """用于预测可能错误的 Pydantic 模型"""
    markdown_content: str = Field(..., description="一个 Markdown 格式的文本，列出并解释了针对该题目可能出现的潜在错误。")

class SolutionDescriptionOutput(BaseModel):
    """用于从代码中提取解法描述的 Pydantic 模型"""
    description: str = Field(..., description="对解法核心逻辑、算法、数据结构和复杂度的简明扼要的描述。")

class GeneralCodeCheckOutput(BaseModel):
    """用于通用代码检查的 Pydantic 模型"""
    error_check_report: str = Field(..., description="一个 Markdown 格式的字符串，列出所有发现的代码错误问题。如果没有错误，则为'未发现代码错误'。")
    optimization_suggestions: str = Field(..., description="一个 Markdown 格式的字符串，列出所有代码优化建议。如果没有建议，则为'无优化建议'。")

class PossibleErrorsOutput(BaseModel):
    """用于预测可能错误的 Pydantic 模型"""
    markdown_content: str = Field(..., description="一个 Markdown 格式的文本，列出并解释了针对该题目可能出现的潜在错误，包括难点、陷阱、概念性错误和实现性错误。")