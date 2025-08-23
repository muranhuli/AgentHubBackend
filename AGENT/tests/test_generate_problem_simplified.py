from AGENT.unit.generate_problem_simplified import generate_problem_simplified

from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
if __name__ == '__main__':
    with Context(router="1234567890", task_id="test_generate_problem_simplified"):
        # 输入
        problem_content = """
城市道路网有 n 个路口，m 条双向道路，每条道路有通行时间 t。
现在要找到从起点 S 到终点 T 的最短时间路径。

输入：
第一行 n, m, S, T
接下来 m 行：每行 u, v, t (表示路口 u 和 v 之间的通行时间 t)

输出：一个整数，表示最短时间；如果不可达输出 -1
"""

# 预期输出
        expected_output = """
## 问题定义

### 输入
- 变量：`n`
- 类型：整数
- 范围：`节点数`
- 变量：`m`
- 类型：整数
- 范围：`边数`
- 变量：`S`
- 类型：整数
- 范围：`起点索引`
- 变量：`T`
- 类型：整数
- 范围：`终点索引`
- 变量：`edges`
- 类型：元组数组
- 范围：`(u, v, t), 1 ≤ u,v ≤ n, t > 0`

### 输出
- 变量：`distance`
- 类型：整数
- 特殊值：`不可达时返回 -1`

### 关系
- `distance = shortest_path(n, edges, S, T)`
"""
        result = generate_problem_simplified(problem_content, "volcengine/doubao-seed-1-6-250615")
        print(result)