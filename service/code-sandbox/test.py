import os

import docker


from template import sandbox_templates
from utils import build_sandbox_cmd, clear_directory, exec_docker


if __name__ == "__main__":

    base_dir = os.path.dirname(os.path.abspath(__file__))
    run_dir = os.path.join(base_dir, "test", "run")
    data_dir = os.path.join(base_dir, "test", "data")
    src_dir = os.path.join(base_dir, "test", "source")
    output_dir = os.path.join(base_dir, "test", "output")

    clear_directory(run_dir)


    container = None
    try:
        client = docker.from_env()
        container = client.containers.run(
            user="root",
            image="code-sandbox",
            name="code-sandbox-test-pycode",
            command="/bin/bash",
            tty=True,  # 交互式终端
            stdin_open=True,  # 保持标准输入打开
            detach=True,  # 后台运行
            pids_limit=32,  # 最多 32 个进程
            mem_limit="4096m",  # 内存上限 4096MiB
            cpu_count=1,  # 使用一个 CPU 核心
            network_disabled=True,  # 完全禁用网络（可选）
            volumes={
                data_dir: {"bind": "/workspace/data", "mode": "ro"},
                src_dir: {"bind": "/workspace/source", "mode": "ro"},
                run_dir: {"bind": "/workspace/run", "mode": "rw"},
                output_dir: {"bind": "/workspace/output", "mode": "rw"}
            }
        )
        exec_docker(container, ["chmod", "777", "/workspace/run"])
        exec_docker(container, ["chmod", "777", "/workspace/output"])

        template_list = [
            "gcc-13.3-cpp-std_17-O2",
            "gcc-13.3-cpp-std_11-O2",
            "gcc-13.3-c-std_11-O2",
            "gcc-13.3-c-std_17-O2",
            "rust-1.78",
            "rust-1.84",
            "pypy-3.10",
            "pypy-3.11",
            "python-3.12",
            "python-3.13",
            "java-8",
            "java-17",
            "java-21"
        ]

        for template in template_list:
            config = sandbox_templates[template]
            clear_directory(run_dir)
            clear_directory(output_dir)
            print(f"Test template: {template}")
            if "compilation" in config:
                compile_cmd = build_sandbox_cmd(
                    exe_path=config["compilation"]["exe_path"],
                    exe_args=config["compilation"]["exe_args"],
                    output_path=config["compilation"].get("output_path", None),
                    max_cpu_time=config["compilation"]["max_cpu_time"],
                    max_real_time=config["compilation"]["max_real_time"],
                    max_memory=config["compilation"]["max_memory"],
                    max_output_size=config["compilation"]["max_output_size"],
                    log_path=config["compilation"]["log_path"],
                )
                exec_docker(container, compile_cmd, "/workspace/run")
            if "run" in config:
                # 预处理 exe_args
                exe_args = config["run"].get("exe_args", [])
                for i in range(len(exe_args)):
                    if "Xmx" in exe_args[i]:
                        exe_args[i] = exe_args[i].format(512)

                run_cmd = build_sandbox_cmd(
                    exe_path=config["run"]["exe_path"],
                    exe_args=exe_args,
                    input_path=config["run"]["input_path"],
                    output_path=config["run"]["output_path"],
                    seccomp_rules=config["run"].get("seccomp_rules", None),
                    max_cpu_time=1000,
                    max_real_time=1000,
                    max_memory= 2048 * 1024 * 1024,  # 2G
                    max_output_size=config["run"]["max_output_size"],
                    log_path=config["run"]["log_path"],
                )
                exec_docker(container, run_cmd, "/workspace/run")

            out = open(f"{output_dir}/output", "r").read()
            out = out.strip()
            if out == "246":
                print("Result:", out)
                print(f"Template {template} executed successfully.\n")
            else:
                print(f"Template {template} execution failed. Output: {out}\n")
                if "compilation" in config:

                    compile_log = open(f"{run_dir}/compilation-sandbox-log.txt", "r").read()
                    print(f"Compilation log:\n{compile_log}")
                if "run"  in config:
                    run_log = open(f"{run_dir}/run-sandbox-log.txt", "r").read()
                    print(f"Run log:\n{run_log}")
                break

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if container:
            container.stop()
            container.remove()