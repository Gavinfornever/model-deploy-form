#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
构建Transformers精简版镜像脚本 - 专为Apple GPU优化
此脚本用于构建能在Apple Silicon (M1/M2/M3) 设备上运行的Transformers精简版Docker镜像
"""

import os
import sys
import argparse
import subprocess
import time
import json

# 镜像基本信息
DEFAULT_IMAGE_NAME = "transformers"
DEFAULT_IMAGE_VERSION = "apple-lite-v1"
DEFAULT_DOCKERFILE = "Dockerfile.apple.lite"

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="构建Transformers精简版Docker镜像 (Apple GPU版)")
    parser.add_argument("--name", type=str, default=DEFAULT_IMAGE_NAME, 
                        help=f"镜像名称 (默认: {DEFAULT_IMAGE_NAME})")
    parser.add_argument("--version", type=str, default=DEFAULT_IMAGE_VERSION, 
                        help=f"镜像版本 (默认: {DEFAULT_IMAGE_VERSION})")
    parser.add_argument("--dockerfile", type=str, default=DEFAULT_DOCKERFILE, 
                        help=f"Dockerfile路径 (默认: {DEFAULT_DOCKERFILE})")
    parser.add_argument("--no-cache", action="store_true", 
                        help="构建时不使用缓存")
    return parser.parse_args()

def run_command(command):
    """运行shell命令并直接显示输出到终端"""
    print(f"执行命令: {command}")
    
    try:
        # 直接将输出显示到终端，不捕获
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False

def check_docker():
    """检查Docker是否可用"""
    print("检查Docker环境...")
    success = run_command("docker --version")
    if not success:
        print("错误: Docker未安装或无法运行")
        sys.exit(1)
    
    # 检查Docker是否正在运行
    success = run_command("docker info > /dev/null 2>&1")
    if not success:
        print("错误: Docker守护进程未运行")
        sys.exit(1)
    
    print("Docker环境检查通过")

def build_image(args):
    """构建Docker镜像"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建完整的镜像名称
    full_image_name = f"{args.name}:{args.version}"
    
    # 构建Dockerfile路径
    dockerfile_path = os.path.join(script_dir, args.dockerfile)
    
    # 检查Dockerfile是否存在
    if not os.path.exists(dockerfile_path):
        print(f"错误: Dockerfile不存在: {dockerfile_path}")
        sys.exit(1)
    
    print(f"\n===== 开始构建镜像: {full_image_name} =====")
    print(f"使用Dockerfile: {dockerfile_path}")
    
    # 构建Docker构建命令
    build_cmd = f"docker build -t {full_image_name} -f {dockerfile_path}"
    
    # 添加--no-cache选项
    if args.no_cache:
        build_cmd += " --no-cache"
    
    # 添加构建上下文
    build_cmd += f" {script_dir}"
    
    # 执行构建命令
    start_time = time.time()
    success = run_command(build_cmd)
    end_time = time.time()
    
    if not success:
        print("镜像构建失败")
        sys.exit(1)
    
    build_time = end_time - start_time
    print(f"镜像构建成功: {full_image_name}")
    print(f"构建用时: {build_time:.2f}秒")
    
    # 保存镜像信息到JSON文件
    image_info = {
        "name": args.name,
        "version": args.version,
        "full_name": full_image_name,
        "build_time": build_time,
        "build_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": "apple",
        "optimized_for": "Apple Silicon (M1/M2/M3)",
        "dockerfile": args.dockerfile
    }
    
    info_file = os.path.join(script_dir, f"{args.name}_{args.version}_info.json")
    with open(info_file, "w") as f:
        json.dump(image_info, f, indent=2)
    
    print(f"镜像信息已保存到: {info_file}")
    
    return full_image_name

def main():
    """主函数"""
    print("===== Transformers精简版Docker镜像构建工具 (Apple GPU版) =====")
    
    # 解析命令行参数
    args = parse_args()
    
    # 检查Docker环境
    check_docker()
    
    # 构建镜像
    image_name = build_image(args)
    
    print("\n===== 构建过程完成 =====")
    print(f"镜像名称: {image_name}")
    print("使用方法:")
    print(f"  docker run --platform=linux/arm64 -it {image_name} python /app/start_model.py --model_name gpt2 --device mps")
    print("注意: 在Apple Silicon设备上运行时，请确保Docker Desktop已配置为使用Rosetta 2")

if __name__ == "__main__":
    main()
