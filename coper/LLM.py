from core.Computable import Computable
from dotenv import load_dotenv
import os
import litellm
import instructor
from typing import Optional
from pydantic import BaseModel, Field
from typing import Union

class LLMResponse(BaseModel):
    """LLM回复的数据类"""
    content: Optional[str] = Field(default="", description="主要回复内容")
    reasoning_content: Optional[str] = Field(default="", description="推理过程内容")
    structured_output: Optional[Union[dict, BaseModel]] = Field(default=None, description="结构化输出")


class LLM(Computable):
    """Call large language models via the LiteLLM library.
    配置逻辑：
    - 若provider为空，则使用litellm配置好的官方信息（使用默认配置）
    - 若provider不为空，则会将provider加入_API_KEY和_BASE_URL前缀去环境变量中寻找
      例如：provider=SDU时，会查找SDU_API_KEY和SDU_BASE_URL环境变量
    - 当使用自定义provider时，模型名会自动加上"openai/"前缀以使用litellm的openai兼容模式
    
    环境变量格式：
    - API密钥：{PROVIDER}_API_KEY
    - 基础URL：{PROVIDER}_BASE_URL
    """

    def __init__(self, model, custom_provider=None):
        super().__init__(model, custom_provider)
        self.model = model
        self.provider = custom_provider
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        if custom_provider is not None:
            self.model = f'openai/{model}'
            self.api_key = os.getenv(f"{custom_provider.upper()}_API_KEY")
            self.base_url = os.getenv(f"{custom_provider.upper()}_BASE_URL")
        else:
            self.api_key = None
            self.base_url = None

    def compute(self, prompt: str, structured_output=None) -> LLMResponse:
        client = instructor.from_litellm(litellm.completion)
        response = client.chat.completions.create(model=self.model,
                                        api_key=self.api_key,
                                        api_base=self.base_url,
                                        response_model=structured_output,
                                        messages=[{"role": "user", "content": prompt}], stream=False)
        llmResponse = LLMResponse(
            content=response["choices"][0]["message"].get("content", "") if structured_output is None else None,
            reasoning_content=response["choices"][0]["message"].get("reasoning_content", "") if structured_output is None else None,
            structured_output=response if structured_output is not None else None
        )
        return llmResponse
