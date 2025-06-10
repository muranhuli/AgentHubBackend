import json
import shutil
from typing import Optional, List

import os


def build_sandbox_cmd(
        exe_path: str,
        exe_args: Optional[List[str]] = None,
        input_path: str = "/dev/stdin",
        output_path: str = "/dev/stdout",
        seccomp_rules: Optional[str] = None,
        max_cpu_time: Optional[int] = None,
        max_real_time: Optional[int] = None,
        max_memory: Optional[int] = None,
        max_stack: Optional[int] = None,
        max_process_number: Optional[int] = None,
        max_output_size: Optional[int] = None,
        log_path: Optional[str] = None,
        exe_envs: Optional[List[str]] = None,
        uid: Optional[int] = None,
        gid: Optional[int] = None,
        print_args: Optional[int]=0
) -> List[str]:
    cmd = ["/usr/bin/sandbox"]

    cmd_t = []
    # required
    cmd_t += [("exe_path", exe_path)]
    # optional single options
    mapping = {
        "input_path": input_path,
        "output_path": output_path,
        "seccomp_rules": seccomp_rules,
        "max_cpu_time": max_cpu_time,
        "max_real_time": max_real_time,
        "max_memory": max_memory,
        "max_stack": max_stack,
        "max_process_number": max_process_number,
        "max_output_size": max_output_size,
        "log_path": log_path,
        "uid": uid,
        "gid": gid,
        "print_args": print_args,
    }
    for opt, val in mapping.items():
        if val is not None:
            cmd_t += [(opt, val)]
    # repeatable list options
    if exe_args:
        for arg in exe_args:
            cmd_t += [("exe_args", arg)]
    if exe_envs:
        for env in exe_envs:
            cmd_t += [("exe_envs", env)]

    for opt, val in cmd_t:
        if isinstance(val, str):
            cmd.append(f"--{opt}=\"{val}\"")
        else:
            cmd.append(f"--{opt}={val}")

    return cmd



def exec_docker(c, cmd: List[str], workdir: str = "/", debug=False):
    """
    Execute a command in a Docker container.
    :param c: The Docker container object.
    :param cmd: The command to execute as a list of strings.
    :param workdir: The working directory inside the container.
    :return: The exit code and output of the command.
    """
    if debug:
        print(f"CMD: {' '.join(cmd)} in {workdir}")
    exec_code, (stdout, stderr) = c.exec_run(cmd, workdir=workdir, stream=False, demux=True)
    if debug:
        print(f"Exit code: {exec_code}")
    if debug and stdout is not None:
        print(f"Stdout: {stdout.decode('utf-8')}")
    if debug and stderr is not None:
        print(f"Stderr: {stderr.decode('utf-8')}")
    return (
        exec_code,
        None if stdout is None else stdout.decode('utf-8'),
        None if stderr is None else stderr.decode('utf-8')
    )


def clear_directory(directory):
    if not os.path.exists(directory):
        return
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.unlink(item_path)
        else:
            shutil.rmtree(item_path)





sandbox_result_map = {
    0: ("SUCCESS", "program finished normally"),
    1: ("CPU_TIME_LIMIT_EXCEEDED", "exceeded CPU time limit"),
    2: ("REAL_TIME_LIMIT_EXCEEDED", "exceeded real time limit"),
    3: ("MEMORY_LIMIT_EXCEEDED", "exceeded memory limit"),
    4: ("RUNTIME_ERROR", "runtime error or killed by signal"),
    5: ("SYSTEM_ERROR", "sandbox system error"),
    6: ("OUTPUT_LIMIT_EXCEEDED", "exceeded output size limit")
}


sandbox_error_map = {
    0: ("SUCCESS", "everything is ok"),
    1: ("INVALID_CONFIG", "invalid config"),
    2: ("FORK_FAILED", "fork() failed"),
    3: ("PTHREAD_FAILED", "thread creation failed"),
    4: ("WAIT_FAILED", "wait4() failed"),
    5: ("DUP2_FAILED", "dup2() failed"),
    6: ("SETRLIMIT_FAILED", "setrlimit() failed"),
    7: ("SETUID_FAILED", "setuid() or setgid() failed"),
    8: ("LOAD_SECCOMP_FAILED", "loading seccomp rules failed"),
    9: ("EXECVE_FAILED", "execve() failed"),
    10: ("PTRACE_FAILED", "ptrace() failed"),
    11: ("SPJ_ERROR", "Special Judge failed"),
    12: ("ROOT_REQUIRED", "sandbox must run as root"),
    13: ("NOBODY_REQUIRED", "user program must run as nobody")
}

def parse_sandbox_output(out: str) -> tuple[dict, dict, dict]:
    # {"cpu_time":12,"real_time":15,"memory":204800,"signal":0,"exit_code":0,"error":0,"result":0}
    out = json.loads(out)
    result, error = {}, {}
    result["tag"] = sandbox_result_map.get(out["result"], ("UNKNOWN", "unknown result"))[0]
    result["msg"] = sandbox_result_map.get(out["result"], ("UNKNOWN", "unknown result"))[1]

    if out["result"] == 5:
        error["tag"] = sandbox_error_map.get(out["error"], ("UNKNOWN", "unknown error"))[0]
        error["msg"] = sandbox_error_map.get(out["error"], ("UNKNOWN", "unknown error"))[1]

    return out, result, error



