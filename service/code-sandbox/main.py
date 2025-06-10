import json
import shutil
import sys
import os
import tempfile
import uuid

import docker
import atexit

from core.Context import Context

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from coper.Minio import Minio
from core.Service import Service
from core.Utils import zip_directory_to_bytes, unzip_bytes_to_directory
from utils import clear_directory, exec_docker, build_sandbox_cmd, parse_sandbox_output
from template import sandbox_templates


class CodeSandbox(Service):

    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config = json.loads(open(config_path).read())
        super().__init__(config["service_id"])
        self.io = None
        self.base_dir = None
        self.run_dir = None
        self.data_dir = None
        self.src_dir = None
        self.output_dir = None
        self.container = None

    def initialize(self):
        self.io = Minio()
        self.base_dir = tempfile.mkdtemp()
        self.run_dir = os.path.join(self.base_dir, "run")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.src_dir = os.path.join(self.base_dir, "source")
        self.output_dir = os.path.join(self.base_dir,"output")

        if not os.path.exists(self.run_dir):
            os.makedirs(self.run_dir)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.src_dir):
            os.makedirs(self.src_dir)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        client = docker.from_env()
        self.container = client.containers.run(
            user="root",
            image="code-sandbox",
            name=f"code-sandbox-{uuid.uuid4().hex[:8]}",
            command="/bin/bash",
            tty=True,  # 交互式终端
            stdin_open=True,  # 保持标准输入打开
            detach=True,  # 后台运行
            pids_limit=16,  # 最多 16 个进程
            mem_limit="4096m",  # 内存上限 4096MiB
            cpu_count=1,  # 使用一个 CPU 核心
            network_disabled=True,  # 完全禁用网络（可选）
            volumes={
                self.data_dir: {"bind": "/workspace/data", "mode": "ro"},
                self.src_dir: {"bind": "/workspace/source", "mode": "ro"},
                self.run_dir: {"bind": "/workspace/run", "mode": "rw"},
                self.output_dir: {"bind": "/workspace/output", "mode": "rw"}
            }
        )
        exec_docker(self.container, ["chmod", "777", "/workspace/run"])
        exec_docker(self.container, ["chmod", "777", "/workspace/output"])



    def close(self):
        shutil.rmtree(self.base_dir)
        self.container.stop()
        self.container.remove(force=True)

    def __cleanup_workspace(self):
        clear_directory(self.run_dir)
        clear_directory(self.data_dir)
        clear_directory(self.src_dir)
        clear_directory(self.output_dir)

    def __get_file(self, f):
        return self.io.compute("read", f["bucket"], f["object_name"])

    def __write_file(self, f, content):
        return self.io.compute("write", f["bucket"], f["object_name"], content)

    def __extract_file(self, src, data, cmd):
        fm = [
            (src, self.src_dir),
            (data, self.data_dir),
            (cmd, self.run_dir)
        ]

        for f, d in fm:
            if not f or not f.get("bucket") or not f.get("object_name"):
                continue
            file = self.__get_file(f)
            if len(file):
                unzip_bytes_to_directory(file, d)


    def __write_output(self, f):
        content = zip_directory_to_bytes(self.output_dir)
        return self.__write_file(f, content)

    def compute(
            self,
            source_file,
            data_file,
            command_file,
            output_file,
            execution_timeout=60,
            execution_memory=256,  # in MB
            sandbox_template="advanced",
    ):
        self.__cleanup_workspace()
        self.__extract_file(source_file, data_file, command_file)
        res = {}
        if sandbox_template != "advanced":
            config = sandbox_templates[sandbox_template]
            if "compilation" in config:
                cc = config["compilation"]
                compile_cmd = build_sandbox_cmd(
                    exe_path=cc["exe_path"],
                    exe_args=cc["exe_args"],
                    output_path=cc.get("output_path", None),
                    max_cpu_time=cc["max_cpu_time"],
                    max_real_time=cc["max_real_time"],
                    max_memory=cc["max_memory"],
                    max_output_size=cc["max_output_size"],
                    log_path=cc["log_path"],
                )
                code, out, err = exec_docker(
                    self.container, compile_cmd, "/workspace/run"
                )
                if code != 0:
                    compile_sandbox_log = open(f"{self.run_dir}/compilation-sandbox-log.txt", "r").read()
                    res["error"] = "System Error while compiling (sandbox error)"
                    res["error_msg"] = f"Code: {code}, Error: {err}, Output: {out}, Log: {compile_sandbox_log}"
                    return res
                else:
                    sandbox_out, sandbox_res, sandbox_err = parse_sandbox_output(out)
                    compile_log = open(f"{self.run_dir}/compilation-output.txt", "r").read()
                    sandbox_out["log"] = compile_log

                    res["compilation"] = sandbox_out

                    if sandbox_out["result"] == 5:
                        compile_sandbox_log = open(f"{self.run_dir}/compilation-sandbox-log.txt", "r").read()
                        res["error"] = "System Error while compiling (compiler error in sandbox)"
                        res["error_msg"] = f"Code: {code}, Error: {err}, Output: {out}, Log: {compile_sandbox_log}, " + \
                                           f"Reason Tag: {sandbox_err['tag']}, Reason: {sandbox_err['msg']}"
                        return res
                    if sandbox_out["result"] != 0:
                        res["error"] = "Compilation Error"
                        res["error_msg"] = f"Reason Tag: {sandbox_res['tag']}, Reason: {sandbox_res['msg']}"
                        return res


            if "run" in config:
                cr = config["run"]
                # 预处理 exe_args
                exe_args = cr.get("exe_args", [])
                for i in range(len(exe_args)):
                    if "Xmx" in exe_args[i]:
                        exe_args[i] = exe_args[i].format(512)

                run_cmd = build_sandbox_cmd(
                    exe_path=cr["exe_path"],
                    exe_args=exe_args,
                    input_path=cr["input_path"],
                    output_path=cr["output_path"],
                    seccomp_rules=cr.get("seccomp_rules", None),
                    max_cpu_time=execution_timeout * 1200,
                    max_real_time=execution_timeout * 1000,
                    max_memory= execution_memory * 1024 * 1024,
                    max_output_size=cr["max_output_size"],
                    log_path=cr["log_path"],
                )
                code, out, err = exec_docker(self.container, run_cmd, "/workspace/run")

                if code != 0:
                    run_sandbox_log = open(f"{self.run_dir}/run-sandbox-log.txt", "r").read()
                    res["error"] = "System Error while running (sandbox error)"
                    res["error_msg"] = f"Code: {code}, Error: {err}, Output: {out}, Log: {run_sandbox_log}"
                else:
                    sandbox_out, sandbox_res, sandbox_err = parse_sandbox_output(out)
                    res["running"] = sandbox_out

                    self.__write_output(output_file)

                    if sandbox_out["result"] != 0:
                        res["error"] = sandbox_res['tag']
                        res["error_msg"] = sandbox_res['msg']
                        if sandbox_out["result"] == 5:
                            run_sandbox_log = open(f"{self.run_dir}/run-sandbox-log.txt", "r").read()
                            res["error_msg"] = (
                                f"{res['error_msg']}\n"
                                f"Log: {run_sandbox_log}, "
                                f"Reason Tag: {sandbox_err['tag']}, "
                                f"Reason: {sandbox_err['msg']}"
                            )

        return res


if __name__ == "__main__":
    with Context():
        service = None
        try:
            service = CodeSandbox()
            atexit.register(service.close)
            service.run()
        finally:
            if service and not atexit._ncallbacks():
                service.close()
