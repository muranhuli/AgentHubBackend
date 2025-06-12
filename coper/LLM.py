from core.Computable import Computable
from dotenv import load_dotenv
import os
import litellm
from typing import Optional, Union, Type
from pydantic import BaseModel, Field, create_model

# 定义JSON Schema类型到Python类型的映射
type_mapping = {
    'string': str,
    'integer': int,
    'number': float,
    'boolean': bool,
    'object': dict,
    'array': list
}


def restore_model_from_schema(schema: dict) -> type[BaseModel]:
    """
    根据JSON Schema恢复Pydantic模型
    """
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


class LLMInput(BaseModel):
    """Input model for LLM operations.
    
    This class defines the structure for inputs to the LLM operator, supporting
    both text-only and multimodal (text + image) interactions with optional
    structured output formatting.
    """
    prompt: str = Field(
        ..., 
        description="The text prompt to send to the LLM model. This is the main instruction or query."
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Optional base64-encoded image data for vision tasks. When provided, enables multimodal processing."
    )
    structured_output: Optional[dict] = Field(
        default=None,
        description="Optional JSON schema for structured output. When provided, the LLM will format its response according to this schema."
    )


class LLMOutput(BaseModel):
    """LLM回复的结构体"""
    content: Optional[str] = Field(default="", description="主要回复内容")
    reasoning_content: Optional[str] = Field(default="", description="推理过程内容")
    structured_output: Optional[Union[dict, BaseModel]] = Field(default=None, description="结构化输出")


class LLM(Computable):
    """LLM operator based on LiteLLM."""

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

    def __init__(self, model: str, custom_provider: Optional[str] = None, system_prompt: Optional[str] = None):
        super().__init__(model, custom_provider)
        self.model = model
        self.provider = custom_provider
        self.system_prompt = system_prompt

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

    def language_llm(self, prompt, structured_model: Optional[type[BaseModel]] = None):
        """Invoke the LLM for language tasks.

        Args:
            prompt: Text prompt sent to the model.
            structured_output: Optional JSON schema describing structured output.

        Returns:
            A dictionary representation of :class:`LLMResponse`.
        """
        # 调用litellm接口
        response = litellm.completion(
            model=self.model,
            api_key=self.api_key,
            api_base=self.base_url,
            allowed_openai_params=['response_format'],
            response_format=structured_model,
            messages=[
                {
                    'role': 'system',
                    'content': self.system_prompt if self.system_prompt else "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=False
        )
        return response

    def vision_llm(self, prompt: str, image_base64: str, structured_model: Optional[type[BaseModel]] = None):
        """Invoke the LLM for vision tasks.

        Args:
            prompt: Text prompt sent to the model.
            image_base64: Base64 encoded image data.

        Returns:
            A dictionary representation of :class:`LLMResponse`.
        """

        # 调用litellm接口
        response = litellm.completion(
            model=self.model,
            api_key=self.api_key,
            api_base=self.base_url,
            allowed_openai_params=['response_format'],
            response_format=structured_model,
            messages=[
                {
                    'role': 'system',
                    'content': self.system_prompt if self.system_prompt else "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_base64}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            stream=False
        )
        return response

    def compute(self, prompt: str, image_base64: Optional[str] = None, structured_output: Optional[dict] = None) -> dict:
        """Invoke the LLM and return the response.

        Args:
            prompt: Text prompt sent to the model.
            structured_output: Optional JSON schema describing structured output.

        Returns:
            A dictionary representation of :class:`LLMResponse`.
        """
        # 若提供了结构化JSON Schema，则将其转换为Pydantic模型
        structured_model: Optional[Type[BaseModel]] = None
        if structured_output:
            structured_model = restore_model_from_schema(structured_output)

        if image_base64 is None:
            llm_response = self.language_llm(prompt, structured_model)
        else:
            llm_response = self.vision_llm(prompt, image_base64, structured_model)

        message = llm_response['choices'][0]['message']
        content = message.get("content", "")
        reasoning = message.get("reasoning_content", "")
        # 若启用结构化输出，则将内容反序列化为模型实例，需针对VLLM进行判断下，VLLM结构化结果在reasoning_content中
        structured = (
            structured_model.model_validate_json(content if content else reasoning).model_dump()
            if structured_model else None
        )

        # 构造统一响应对象
        llm_response = LLMOutput(
            content=content if not structured_model else None,
            reasoning_content=reasoning if not structured_model else None,
            structured_output=structured
        )

        return llm_response.model_dump()
