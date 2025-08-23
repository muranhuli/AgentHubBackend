from AGENT.unit.get_problem_details import get_problem_details

from coper.LLM import LLM
from coper.basic_ops import Mul
from core.Context import Context
from coper.Service import Service
import getpass
import logging
from AGENT.unit.oj_log_in import login
import requests
if __name__ == '__main__':
    with Context(router="1234567890", task_id="test_get_problem_details"):
        username = input("请输入您的 SDUOJ 用户名: ")
        password = getpass.getpass("请输入您的 SDUOJ 密码: ")
        session = requests.Session()
        login(session, username, password)
        if not login(session, username, password):
            sys.exit(1)
        problem_code = "SDUOJ-1204"
        details = get_problem_details(session, problem_code)
        print("Problem Details:", details)