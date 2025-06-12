import argparse
import os
import platform
import subprocess
import sys

def abort(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)

def get_service_dir(name):
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, name)
    if not os.path.isdir(path):
        abort(f"service directory '{name}' not found")
    return path

def run_cmd(cmd, cwd):
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        abort(f"command failed (exit {e.returncode}): {' '.join(cmd)}")

def build_command(cmd_name, script_path, extra_args):
    if cmd_name in ('install', 'remove'):
        if script_path.endswith('.ps1'):
            return ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path] + extra_args
        return ['bash', script_path] + extra_args
    # start 用 Python 解释器直接跑 main.py
    return [sys.executable, script_path] + extra_args

def main():
    p = argparse.ArgumentParser(description='Deploy tool')
    p.add_argument('command', choices=['install', 'remove', 'start'])
    p.add_argument('service', help='service subfolder name')
    p.add_argument('extra', nargs=argparse.REMAINDER,
                   help='arguments to pass through')
    args = p.parse_args()

    svc_dir = get_service_dir(args.service)
    is_windows = platform.system().lower().startswith('win')
    ext = 'ps1' if is_windows else 'sh'

    # 确定脚本文件
    if args.command in ('install', 'remove'):
        script_file = f"{args.command}.{ext}"
    else:  # start
        script_file = 'main.py'

    script_path = os.path.join(svc_dir, script_file)
    if not os.path.isfile(script_path):
        abort(f"'{script_file}' missing in {svc_dir}")

    # 构造并执行命令
    cmd = build_command(args.command, script_path, args.extra)
    run_cmd(cmd, cwd=svc_dir)

if __name__ == '__main__':
    main()
