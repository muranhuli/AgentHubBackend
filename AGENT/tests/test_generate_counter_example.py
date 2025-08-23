from AGENT.unit.generate_counter_example import generate_counter_example

from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
if __name__ == '__main__':
    with Context(router="1234567890", task_id="test_judge_error_type"):
        problem_desc="""
        ## 问题定义

### 输入
- 变量：`T`, `N`
- 类型：整数
- 范围：`1 ≤ T`, `1 ≤ N ≤ 1000`

### 输出
- 变量：`P`
- 类型：实数
- 范围：`0 ≤ P ≤ 1`

### 关系
- `P = (2^(N-1) * (N-1)! ) / ( (2N-1)!! )`
        """
        student_code = """
#include <iostream>
#include <vector>
#include <algorithm>
#include <iomanip>

using namespace std;

// 计算单个同学的得分：去掉一个最高、一个最低，求平均
double calculateScore(vector<int> scores) {
    sort(scores.begin(), scores.end());
    // 这里故意没处理 m < 2 的极端情况，算一个小问题，实际题目里 m≥1 但题目说 m≤20，正常输入会保证 m≥2 吗？代码没做防御
    int sum = 0;
    for (int i = 1; i < scores.size() - 1; i++) { 
        sum += scores[i];
    }
    return (double)sum / (scores.size() - 2);
}

int main() {
    int n, m;
    cin >> n >> m;

    double maxScore = 0.0;
    for (int i = 0; i < n; i++) {
        vector<int> s;
        for (int j = 0; j < m; j++) {
            int score;
            cin >> score;
            s.push_back(score);
        }
        double current = calculateScore(s);
        if (current > maxScore) {
            maxScore = current;
        }
    }

    cout << fixed << setprecision(2) << maxScore << endl;
    return 0;
}
"""
        error_analysis = {

'error_type': 'conceptual',

'reasoning': '1. 学生代码解决的问题与题目要求完全不符。题目要求计算一个特定的数学表达式 P = (2^(N-1) * (N-1)! ) / ((2N-1)!!)，而学生代码实现的是"去掉最高最低分求平均分并找最大值"的功能。\n\n2. 这是一个根本性的概念错误，学生可能错误理解了题目要求，或者将另一个不相关问题的解决方案提交到了这个问题上。\n\n3. 代码本身的结构和逻辑是针对完全不同的竞赛评分问题，而不是题目要求的数学公式计算。代码中完全没有实现题目要求的阶乘、双阶乘或指数运算。\n\n4. 实现细节上虽然有一些小问题(如未处理m<2的情况)，但主要错误在于选择了完全错误的算法和解决方案，属于概念性错误而非实现性错误。'

}
        result = generate_counter_example(problem_desc, student_code,error_analysis,"volcengine/doubao-seed-1-6-250615")
        print(result)
