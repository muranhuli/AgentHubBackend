from AGENT.unit.general_code_check import general_code_check

from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
if __name__ == '__main__':
    with Context(router="123", task_id="test_general_code_check"):
        print("请输入待检查的C++代码\n")
        print("\n[INPUT] Enter C++ code line by line. Type 'ENDCODE' on a new line to finish.")
        cpp_code_lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "ENDCODE":
                    print("[DEBUG] 'ENDCODE' received. Finishing code input.")
                    break
                cpp_code_lines.append(line)
            except EOFError:
                print("[DEBUG] EOFError received. Finishing code input.")
                break

        cpp_code = "\n".join(cpp_code_lines)
        result = general_code_check(cpp_code,"deepseek/deepseek-chat")
        print(result)





       