import os
import shutil
from typing import Optional, List


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



def exec_docker(c, cmd: List[str], workdir: str = "/"):
    """
    Execute a command in a Docker container.
    :param c: The Docker container object.
    :param cmd: The command to execute as a list of strings.
    :param workdir: The working directory inside the container.
    :return: The exit code and output of the command.
    """
    print(f"CMD: {' '.join(cmd)} in {workdir}")
    exec_code, (stdout, stderr) = c.exec_run(cmd, workdir=workdir, stream=False, demux=True)
    print(f"Exit code: {exec_code}")
    if stdout is not None:
        print(f"Stdout: {stdout.decode('utf-8')}")
    if stderr is not None:
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