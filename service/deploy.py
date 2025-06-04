#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
import yaml

def error_exit(message):
    print(f"错误：{message}", file=sys.stderr)
    sys.exit(1)

def check_conda():
    if shutil.which("conda") is None:
        error_exit("未检测到 Conda，可通过安装 Anaconda 或 Miniconda 来使用此脚本。")

def conda_env_exists(env_name):
    try:
        result = subprocess.run(
            ["conda", "env", "list", "--json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        data = json.loads(result.stdout)
        return any(os.path.basename(path) == env_name for path in data.get("envs", []))
    except subprocess.CalledProcessError as e:
        error_exit(f"执行 `conda env list` 失败：{e.stderr.strip()}")

def extract_env_name(env_file_path):
    if not os.path.isfile(env_file_path):
        error_exit(f"未找到 environment.yml：{env_file_path}")
    with open(env_file_path, "r", encoding="utf-8") as f:
        env_data = yaml.safe_load(f)
    name = env_data.get("name")
    if not name:
        error_exit(f"未在 {env_file_path} 中找到 Conda 环境名称字段 'name'")
    return name

def create_conda_env(env_file, env_name):
    print(f"创建 Conda 环境：{env_name}（从 {env_file}）")
    try:
        subprocess.run(
            ["conda", "env", "create", "-f", env_file],
            check=True
        )
    except subprocess.CalledProcessError as e:
        error_exit(f"创建环境失败：{e}")

def run_init_script(env_name, script_path):
    if not os.path.isfile(script_path):
        error_exit(f"初始化脚本未找到：{script_path}")
    print(f"在环境 {env_name} 中执行初始化脚本：{script_path}")
    try:
        subprocess.run(
            ["conda", "run", "-n", env_name, "bash", script_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        error_exit(f"执行初始化脚本失败：{e}")

def pip_install_requirements(env_name, requirements_path):
    if not os.path.isfile(requirements_path):
        print(f"警告：未找到补充依赖文件 {requirements_path}，跳过 pip 安装。")
        return
    print(f"在环境 {env_name} 中通过 pip 安装：{requirements_path}")
    try:
        subprocess.run(
            ["conda", "run", "-n", env_name, "pip", "install", "-r", requirements_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        error_exit(f"pip 安装失败：{e}")

def load_config(config_path):
    if not os.path.isfile(config_path):
        error_exit(f"配置文件未找到：{config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def install_service(service_id: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    service_dir = os.path.join(base_dir, service_id)
    if not os.path.isdir(service_dir):
        error_exit(f"服务目录不存在：{service_dir}")

    config_path = os.path.join(service_dir, "config.json")
    config = load_config(config_path)
    deploy_cfg = config.get("deploy", {})

    if deploy_cfg.get("mode") != "conda":
        error_exit(f"不支持的部署模式：{deploy_cfg.get('mode')}")

    env_file = os.path.join(service_dir, deploy_cfg.get("config_file", ""))
    init_script = os.path.join(service_dir, deploy_cfg.get("init_script", ""))
    env_name = extract_env_name(env_file)

    check_conda()

    if not conda_env_exists(env_name):
        create_conda_env(env_file, env_name)
        run_init_script(env_name, init_script)
    else:
        print(f"已存在 Conda 环境：{env_name}，跳过创建。")

    requirements_path = os.path.join(os.path.dirname(base_dir), "requirements.txt")
    pip_install_requirements(env_name, requirements_path)

    print(f"服务 {service_id} 部署完成。")

def main():
    parser = argparse.ArgumentParser(description="部署工具")
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install", help="部署并启动服务")
    install_parser.add_argument("service_id", help="服务子目录名称（如 local-web-search）")

    args = parser.parse_args()

    if args.command == "install":
        install_service(args.service_id)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
