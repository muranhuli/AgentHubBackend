from AGENT.unit.extract_solution_from_code import extract_solution_from_code

from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
if __name__ == '__main__':
    with Context(router="1234567890", task_id="test_extract_solution_from_code"):
        # 输入
        code = """
class Solution:
    def maxArea(self, height: List[int]) -> int:
        left, right = 0, len(height) - 1
        max_area = 0
        
        while left < right:
            h = min(height[left], height[right])
            area = h * (right - left)
            max_area = max(max_area, area)
            
            if height[left] < height[right]:
                left += 1
            else:
                right -= 1
                
        return max_area
"""

        problem_desc = "盛最多水的容器问题"

# 预期输出
        expected_output = {
    "description": "使用双指针法计算最大容水量。左右指针从两端开始，计算当前面积后移动较矮的指针。时间复杂度O(n)，空间复杂度O(1)。",
    "code": code.strip()
}
        model="volcengine/doubao-seed-1-6-250615"
        result = extract_solution_from_code(code, problem_desc,model)
        print(result)