#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
本地模型运行脚本 - 用于在Docker容器中运行本地模型
此脚本简化了本地模型的挂载和运行过程
"""

import os
import sys
import argparse
import subprocess
import time

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="在Docker容器中运行本地模型")
    parser.add_argument("--model_path", type=str, required=True, 
                        help="本地模型路径，例如: /Users/username/models/Qwen2.5-0.5B")
    parser.add_argument("--image", type=str, default="transformers:apple-lite-v1", 
                        help="Docker镜像名称")
    parser.add_argument("--device", type=str, default="mps", 
                        help="运行设备 (cpu, mps)")
    parser.add_argument("--port", type=str, default="8000", 
                        help="API服务端口")
    parser.add_argument("--name", type=str, default="", 
                        help="容器名称，默认自动生成")
    return parser.parse_args()

def run_command(command):
    """运行shell命令"""
    print(f"执行命令: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False

def main():
    """主函数"""
    args = parse_args()
    
    # 获取模型路径和名称
    model_path = os.path.abspath(args.model_path)
    model_name = os.path.basename(model_path)
    
    if not os.path.exists(model_path):
        print(f"错误: 模型路径不存在: {model_path}")
        sys.exit(1)
    
    # 构建容器名称
    container_name = args.name if args.name else f"model-{model_name}-{int(time.time())}"
    
    # 构建运行命令
    cmd = f"""
    docker run --platform=linux/arm64 -it --rm \
      --name {container_name} \
      -v {model_path}:/app/models/local_model \
      -p {args.port}:8000 \
      {args.image} \
      python /app/start_model.py \
        --model_name /app/models/local_model \
        --device {args.device} \
        --port 8000 \
        --host 0.0.0.0
    """
    
    print("\n===== 启动本地模型容器 =====")
    print(f"模型路径: {model_path}")
    print(f"模型名称: {model_name}")
    print(f"容器名称: {container_name}")
    print(f"使用镜像: {args.image}")
    print(f"运行设备: {args.device}")
    print(f"API端口: {args.port}")
    print("\n启动容器...")
    
    # 运行命令
    run_command(cmd)

if __name__ == "__main__":
    main()
