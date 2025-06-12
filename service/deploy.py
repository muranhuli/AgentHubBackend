#!/usr/bin/env python3
import argparse
import json
import os
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

def main():
    p = argparse.ArgumentParser(description='Deploy tool')
    p.add_argument('command', choices=['install', 'remove', 'start'])
    p.add_argument('service', help='service subfolder name')
    p.add_argument('extra', nargs=argparse.REMAINDER,
                   help='arguments to pass through')
    args = p.parse_args()

    svc_dir = get_service_dir(args.service)

    if args.command in ('install', 'remove'):
        script = os.path.join(svc_dir, f"{args.command}.sh")
        if not os.path.isfile(script):
            abort(f"'{args.command}.sh' missing in {svc_dir}")
        cmd = ['bash', script] + args.extra

    else:  # start
        cfg_path = os.path.join(svc_dir, 'config.json')
        custom = None
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, encoding='utf-8') as f:
                    cfg = json.load(f)
                custom = cfg.get('start', {}).get('script')
            except Exception as e:
                abort(f"failed to parse config.json: {e}")

        if custom:
            # combine the command string and extra args
            full = custom + (' ' + ' '.join(args.extra) if args.extra else '')
            cmd = ['bash', '-c', full]
        else:
            main_py = os.path.join(svc_dir, 'main.py')
            if not os.path.isfile(main_py):
                abort(f"'main.py' missing in {svc_dir}")
            cmd = [sys.executable, main_py] + args.extra

    run_cmd(cmd, cwd=svc_dir)

if __name__ == '__main__':
    main()
