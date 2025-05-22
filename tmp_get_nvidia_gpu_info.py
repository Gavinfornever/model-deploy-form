#!/usr/bin/env python3
import paramiko
import json
import re
import sys

def get_gpu_info(hostname, port, username, password):
    """获取远程服务器上的NVIDIA GPU信息"""
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 连接到远程服务器
        print(f"正在连接到远程服务器 {hostname}...")
        ssh.connect(hostname, port, username, password)
        print("连接成功！")
        
        # 执行nvidia-smi命令获取GPU信息
        print("正在获取GPU信息...")
        stdin, stdout, stderr = ssh.exec_command("nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader")
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")
        
        if error:
            print(f"执行命令时出错: {error}")
            
        # 解析输出
        gpus = []
        lines = output.strip().split("\n")
        print(f"原始输出: {lines}")
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split(", ")
            if len(parts) >= 3:
                index = parts[0].strip()
                name = parts[1].strip()
                memory = parts[2].strip()
                driver_version = parts[3].strip() if len(parts) > 3 else "Unknown"
                cuda_version = parts[4].strip() if len(parts) > 4 else "Unknown"
                
                # 提取内存大小（去除MiB或MB后缀）
                memory_match = re.search(r'(\d+)', memory)
                memory_total = int(memory_match.group(1)) if memory_match else 0
                
                # 创建GPU信息字典
                gpu = {
                    "index": index,
                    "name": name,
                    "memory_total": memory_total,
                    "driver_version": driver_version,
                    "cuda_version": cuda_version
                }
                gpus.append(gpu)
        
        return gpus
        
    except Exception as e:
        print(f"获取GPU信息时出错: {e}")
        return []
    finally:
        ssh.close()

def main():
    # 远程服务器信息
    hostname = "47.116.124.254"
    port = 22
    username = "root"
    password = "wW650803"
    
    # 获取GPU信息
    gpus = get_gpu_info(hostname, port, username, password)
    
    # 输出结果
    if gpus:
        print(f"\n发现 {len(gpus)} 个NVIDIA GPU:")
        for gpu in gpus:
            print(f"  - GPU {gpu['index']}: {gpu['name']}, 内存: {gpu['memory_total']}MB, 驱动: {gpu['driver_version']}, CUDA: {gpu['cuda_version']}")
    else:
        print("未发现任何NVIDIA GPU")

if __name__ == "__main__":
    main()
