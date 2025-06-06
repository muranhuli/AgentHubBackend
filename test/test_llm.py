import numpy as np
import random
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
        # llm = LLM("DeepSeek-R1", 'SDU')
        llm = LLM("doubao-1-5-thinking-pro-250415", "ARK")

        # 1. 测试 LLM 的计算功能
        # prompt = "Where is the capital of France?"
        prompt = "Write a Python function to calculate the factorial of a number."
        response1 = llm.compute(prompt, CodeAnswer)
        # response1 = llm(prompt, CodeAnswer).result() # 序列化完成可以执行这个
        print(f"Prompt: {prompt}\ntype: {type(response1)}\nResponse:\n{response1}")
        end = time.time()
        print(f"Total time taken: {end - start:.2f} seconds")
