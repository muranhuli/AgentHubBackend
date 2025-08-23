from AGENT.unit.judge_error_type import judge_error_type

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
        
        result = judge_error_type(problem_desc, student_code, "volcengine/doubao-seed-1-6-250615")
        print(result)
