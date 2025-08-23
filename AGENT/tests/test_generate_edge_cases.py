from AGENT.unit.generate_edge_cases import generate_edge_cases

from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
if __name__ == '__main__':
    with Context(router="1234567890", task_id="test_generate_problem_simplified"):
        # 输入
        problem_desc = """
## 问题定义

### 输入
- 变量：`n`, `m`
- 类型：整数
- 范围：`1 ≤ n ≤ 10000, 0 ≤ m ≤ 200000`
- 变量：`edges`
- 类型：元组数组
- 范围：`(u, v, w), 1 ≤ u,v ≤ n, 0 ≤ w ≤ 10^9`

### 输出
- 变量：`dist`
- 类型：整数数组
- 特殊值：`不可达时为 -1`

### 关系
- 求起点1到所有点的最短路径
"""

# 预期输出（模拟 LLM 返回）
        expected_output = """
# 边缘测试用例

用例 1: 零边图
• 输入: 
  n=1, m=0
  edges=[]
• 预期输出: 
  [0]
• 设计理由: 测试最小图的边界情况

用例 2: 单节点自环
• 输入: 
  n=1, m=1
  edges=[(1,1,5)]
• 预期输出: 
  [0]
• 设计理由: 测试自环特殊情况

用例 3: 大规模图
• 输入: 
  n=10000, m=200000
  edges=完全连接图的随机子集
• 预期输出: 
  #省略具体值#
• 设计理由: 测试时间复杂度和内存管理
"""
        result = generate_edge_cases(problem_desc, "volcengine/doubao-seed-1-6-250615")
        print(result)