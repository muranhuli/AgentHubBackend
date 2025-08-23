
import requests
from AGENT.unit.submit_solution import submit_solution
from AGENT.unit.oj_log_in import login
from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import logging
import getpass
#from sduoj_client import submit_solution
BASE_URL = "https://oj.qd.sdu.edu.cn"
PROBLEM_CODE = "SDUOJ-1204"
if __name__ == "__main__":
    with Context(router="1234567890",task_id="test_submit_solution"):
        # username = input("请输入您的 SDUOJ 用户名: ")
        # password = getpass.getpass("请输入您的 SDUOJ 密码: ")
        username="202300130111"
        password="1517287203Syx"
        session = requests.Session()
        login(session, username, password)
        if not login(session, username, password):
            sys.exit(1)

        code = r'''
#include <iostream>
int main() {
    std::cout << "hello\n";
    return 0;
}
    '''
        sid = submit_solution(session,
                          problem_id="1204",
                          code=code,
                          language="C++14")
        print("Submission ID:", sid)