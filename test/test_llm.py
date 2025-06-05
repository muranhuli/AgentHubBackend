import numpy as np
import random
from core.Context import Context
import uuid
from coper.LLM import LLM
import time

if __name__ == "__main__":
    with Context(task_id=str(uuid.uuid4().hex)) as ctx:
        start = time.time()
        # 使用 LLM 类
        llm = LLM(model="openai/DeepSeek-R1")

        # 1. 测试 LLM 的计算功能
        prompt = "What is the capital of France?"
        response1 = llm(prompt)
        print(f"Prompt: {prompt}\nResponse: {response1.result()}")
        
        # 2. 测试不同模型的调用
        llm2 = LLM(model="openai/DeepSeek-R1")
        prompt = "What is the capital of China?"
        response2 = llm2(prompt)
        

        print(f"Prompt: {prompt}\nResponse from openai/DeepSeek-R1: {response2.result()}")
        end = time.time()
        print(f"Total time taken: {end - start:.2f} seconds")
