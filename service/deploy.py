#!/usr/bin/env python3
import argparse
import json
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

def build_shell_command(script_str, extra_args, use_powershell):
    if use_powershell:
        # PowerShell -Command 会把整个字符串当作一条命令执行
        return ['powershell', '-ExecutionPolicy', 'Bypass', '-Command',
                script_str + (' ' + ' '.join(extra_args) if extra_args else '')]
    else:
        return ['bash', '-c',
                script_str + (' ' + ' '.join(extra_args) if extra_args else '')]

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

    if args.command in ('install', 'remove'):
        script_file = f"{args.command}.{ext}"
        script_path = os.path.join(svc_dir, script_file)
        if not os.path.isfile(script_path):
            abort(f"'{script_file}' missing in {svc_dir}")
        if is_windows:
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path] + args.extra
        else:
            cmd = ['bash', script_path] + args.extra

    else:  # start
        # 尝试读取 config.json 中的自定义 start.script
        config_path = os.path.join(svc_dir, 'config.json')
        custom = None
        if os.path.isfile(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                start_cfg = cfg.get('start', {})
                custom = start_cfg.get('script')
            except Exception as e:
                abort(f"failed to parse config.json: {e}")

        if custom:
            cmd = build_shell_command(custom, args.extra, is_windows)
        else:
            # 回退到 main.py
            script_path = os.path.join(svc_dir, 'main.py')
            if not os.path.isfile(script_path):
                abort(f"'main.py' missing in {svc_dir}")
            cmd = [sys.executable, script_path] + args.extra

    run_cmd(cmd, cwd=svc_dir)

if __name__ == '__main__':
    main()
