from core.Context import Context
import uuid
from coper.LLM import LLM
import time
from pydantic import BaseModel, Field


class CodeAnswer(BaseModel):
    """LLM回答的模型"""
    code: str = Field(description="Only the code part is output, without any other output")
    content: str = Field(description="Explain the code")


if __name__ == "__main__":
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        start = time.time()
        # 使用 LLM 类
        # llm = LLM("volcengine/doubao-1-5-lite-32k-250115")
        # llm = LLM("volcengine/doubao-1-5-thinking-pro-250415")
        llm_vision = LLM("doubao-1-5-thinking-vision-pro-250428", "ARK")
        llm_language = LLM("Qwen3-32B", "VLLM")

        # 视觉大模型测试
        prompt = "回答这个图片，说明这个图片做了什么？请用中文回答。"
        response1 = llm_vision(prompt, './test/test.jpg', structured_output=CodeAnswer.model_json_schema()).result()
        print(f"Prompt: {prompt}\ntype: {type(response1)}\nResponse:\n{response1}")
        print('='*50)

        # 语言大模型测试
        prompt = "写一个Python函数，计算两个数的和，并返回结果。请用中文回答。"
        response1 = llm_language(prompt, structured_output=CodeAnswer.model_json_schema()).result()
        print(f"Prompt: {prompt}\ntype: {type(response1)}\nResponse:\n{response1}")

        end = time.time()
        print(f"Total time taken: {end - start:.2f} seconds")
