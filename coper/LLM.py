from core.Computable import Computable
from dotenv import load_dotenv
import os
import litellm
from typing import Optional, Union, Type
from pydantic import BaseModel, Field, create_model

type_mapping = {
    'string': str,
    'integer': int,
    'number': float,
    'boolean': bool,
    'object': dict,
    'array': list
}


def restore_model_from_schema(schema: dict) -> type[BaseModel]:
    '''
        根据JSON Schema恢复Pydantic模型
    '''
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields = {}

    for name, prop in props.items():
        ptype = type_mapping.get(prop.get("type"), str)  # 默认str
        description = prop.get("description", "")
        default = ... if name in required else None  # 必填用 Ellipsis
        fields[name] = (ptype, Field(default, description=description))

    model_name = schema.get("title", "DynamicModel")
    return create_model(model_name, **fields)


class LLMResponse(BaseModel):
    """LLM回复的结构体"""
    content: Optional[str] = Field(default="", description="主要回复内容")
    reasoning_content: Optional[str] = Field(default="", description="推理过程内容")
    structured_output: Optional[Union[dict, BaseModel]] = Field(default=None, description="结构化输出")


class LLM(Computable):
    """
    基于LiteLLM封装的LLM调用类。

    配置逻辑说明：
    - 若custom_provider为空，使用默认配置。
    - 若custom_provider非空：
        - 模型名自动加前缀 "openai/"，启用openai兼容模式；
        - 自动从环境变量中读取{PROVIDER}_API_KEY和{PROVIDER}_BASE_URL。

    环境变量格式要求：
    - API密钥：{PROVIDER}_API_KEY
    - 基础URL：{PROVIDER}_BASE_URL
    """

    def __init__(self, model: str, custom_provider: Optional[str] = None):
        super().__init__(model, custom_provider)
        self.model = model
        self.provider = custom_provider

        # 加载环境变量
        self._load_env()

        # 配置自定义Provider参数
        if self.provider:
            self.model = f"openai/{model}"
            provider_upper = self.provider.upper()
            self.api_key = os.getenv(f"{provider_upper}_API_KEY")
            self.base_url = os.getenv(f"{provider_upper}_BASE_URL")
        else:
            self.api_key = None
            self.base_url = None

    def _load_env(self):
        """加载项目根目录下的.env文件"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)

    def compute(self, prompt: str, structured_output: Optional[dict] = None) -> dict:
        """
        调用LLM并返回结果。

        :param prompt: 用户输入的提示词
        :param structured_output: 若需要结构化输出，传入Pydantic模型类
        :return: 返回标准结构的LLMResponse字典
        """
        # 若提供了结构化JSON Schema，则将其转换为Pydantic模型
        structured_model: Optional[Type[BaseModel]] = None
        if structured_output:
            structured_model = restore_model_from_schema(structured_output)

        # 调用litellm接口
        response = litellm.completion(
            model=self.model,
            api_key=self.api_key,
            api_base=self.base_url,
            response_format=structured_model,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        print(f"LLM response: {response}")
        message = response['choices'][0]['message']
        content = message.get("content", "")
        reasoning = message.get("reasoning_content", "")

        # 若启用结构化输出，则将内容反序列化为模型实例，需针对VLLM进行判断下，VLLM结构化结果在reasoning_content中
        structured = (
            structured_model.model_validate_json(content if content else reasoning).model_dump()
            if structured_model else None
        )

        # 构造统一响应对象
        llm_response = LLMResponse(
            content=content if not structured_model else None,
            reasoning_content=reasoning if not structured_model else None,
            structured_output=structured
        )

        return llm_response.model_dump()
