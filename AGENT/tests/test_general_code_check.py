from AGENT.unit.general_code_check import general_code_check

from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
if __name__ == '__main__':
    with Context(router="1234567890", task_id="test_general_code_check"):
        # 输入
#         student_code = """
# import threading

# counter = 0
# lock = threading.Lock()

# def increment():
#     global counter
#     for _ in range(100000):
#         lock.acquire()
#         counter += 1
#         # 缺少release，资源泄漏
    
# threads = []
# for i in range(10):
#     t = threading.Thread(target=increment)
#     t.start()
#     threads.append(t)

# for t in threads:
#     t.join()

# print(counter)
# """
        student_code = """
        int a
        cout<<b
        """
# 模拟 LLM 返回
        llm_response = """
## 代码错误检查
1. 资源泄漏：锁对象未释放，导致死锁
2. 异常安全问题：未使用上下文管理器(with lock)
3. 全局变量使用：线程共享的全局变量可能有竞态条件风险

## 优化建议
1. 使用 with lock: 自动管理资源
2. 避免全局变量：使用传递参数的方式
3. 原子操作：使用 threading.Lock 或 queue 替代共享变量
4. 添加错误处理：捕获线程异常
"""
        result = general_code_check(student_code, "volcengine/doubao-seed-1-6-250615")
        print(result)