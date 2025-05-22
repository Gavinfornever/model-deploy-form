#!/usr/bin/env python3
import requests
import json
import sys
import paramiko
import time

def main():
    # 集群ID
    cluster_id = "86a8ff8e-fc48-4e1f-bc7d-d1663a3fbbb2"
    
    # 远程服务器信息
    hostname = "47.116.124.254"
    port = 22
    username = "root"
    password = "wW650803"
    
    # 中心控制器URL
    center_controller_url = "http://localhost:5001"
    
    # 获取集群信息
    response = requests.get(f"{center_controller_url}/api/clusters/{cluster_id}")
    if response.status_code != 200:
        print(f"获取集群信息失败: {response.text}")
        return
    
    cluster_info = response.json()["data"]
    print(f"集群信息: {json.dumps(cluster_info, indent=2, ensure_ascii=False)}")
    
    # 连接到远程服务器
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname, port, username, password)
        print(f"成功连接到远程服务器 {hostname}")
        
        # 获取NVIDIA GPU信息
        stdin, stdout, stderr = ssh.exec_command("nvidia-smi --query-gpu=index,name,memory.total,utilization.gpu --format=csv,noheader")
        gpu_info_lines = stdout.read().decode().strip().split("\n")
        
        # 解析GPU信息
        gpus = []
        for line in gpu_info_lines:
            parts = line.split(", ")
            if len(parts) >= 3:
                index = parts[0].strip()
                name = parts[1].strip()
                memory = parts[2].strip().replace(" MiB", "")
                gpu = {
                    "id": f"gpu-{index}",
                    "name": name,
                    "memory": int(memory),
                    "status": "available"
                }
                gpus.append(gpu)
        
        print(f"发现 {len(gpus)} 个NVIDIA GPU: {json.dumps(gpus, indent=2, ensure_ascii=False)}")
        
        # 创建节点信息
        node = {
            "id": "iZuf6hfr6d5n63lo5udfekZ",
            "name": "iZuf6hfr6d5n63lo5udfekZ",
            "ip": hostname,
            "status": "online",
            "gpus": gpus
        }
        
        # 注册节点到集群
        response = requests.post(
            f"{center_controller_url}/api/clusters/{cluster_id}/nodes",
            json=node
        )
        
        if response.status_code == 200:
            print(f"成功注册节点到集群: {response.text}")
        else:
            print(f"注册节点失败: {response.text}")
        
    except Exception as e:
        print(f"操作失败: {str(e)}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
