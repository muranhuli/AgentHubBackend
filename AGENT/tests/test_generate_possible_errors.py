from AGENT.unit.generate_possible_errors import generate_possible_errors

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
- 范围：`1 ≤ n ≤ 500, 0 ≤ m ≤ 10000`
- 变量：`edges`
- 类型：元组数组
- 范围：`(u, v, w), 1 ≤ u,v ≤ n, 1 ≤ w ≤ 1000`

### 输出
- 变量：`distances`
- 类型：整数数组
- 长度：`n`
- 特殊值：`不可达节点值为 -1`

### 关系
- 求从节点1到所有节点的最短路径
"""

# 预期输出（模拟 LLM 返回）
        expected_output = """
# 潜在错误分析

1. **主要难点与陷阱**
   - 负权边（但题目要求w>0）
   - 大O复杂度分析
   - 自环和多边的处理

2. **概念性错误**
   - 错误1: 错误选择算法
     - 示例代码:
        // 尝试在非负权图中使用SPFA
     - 原因分析: Dijkstra算法更适合此场景
     - 避免建议: 根据问题约束选择合适算法

3. **实现性错误**
   - 错误1: 未重置前节点值
     - 示例代码:
        // 重复使用dist数组未清零
     - 原因分析: 多测试案例共享状态导致错误
     - 避免建议: 为每个测试案例初始化数据结构
   
   - 错误2: 无穷大值选择不当
     - 示例代码:
        int INF = 100000; // 不够大
     - 原因分析: w最大值1000*n节点数可能超过100000
     - 避免建议: 使用INT_MAX或更安全的无穷大表示
"""

        result = generate_possible_errors(problem_desc, "volcengine/doubao-seed-1-6-250615")
        print(result)