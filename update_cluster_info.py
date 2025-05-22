#!/usr/bin/env python3
import requests
import json
import sys
import paramiko
import time
import re

def get_system_info(hostname, port, username, password):
    """获取远程服务器的系统信息，包括内存、CPU和GPU"""
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 连接到远程服务器
        print(f"正在连接到远程服务器 {hostname}...")
        ssh.connect(hostname, port, username, password)
        print("连接成功！")
        
        # 获取系统信息
        system_info = {}
        
        # 获取内存信息
        print("正在获取内存信息...")
        stdin, stdout, stderr = ssh.exec_command("free -m | grep Mem")
        mem_output = stdout.read().decode("utf-8")
        mem_parts = mem_output.split()
        if len(mem_parts) >= 7:
            system_info["memory_total"] = int(mem_parts[1])
            system_info["memory_available"] = int(mem_parts[6])
        
        # 获取CPU信息
        print("正在获取CPU信息...")
        stdin, stdout, stderr = ssh.exec_command("lscpu")
        cpu_output = stdout.read().decode("utf-8")
        
        # 解析CPU信息
        cpu_info = {}
        for line in cpu_output.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                cpu_info[key.strip()] = value.strip()
        
        # 提取关键信息
        system_info["cpu_info"] = {
            "model": cpu_info.get("Model name", "Unknown"),
            "cores": int(cpu_info.get("CPU(s)", 0)),
            "architecture": cpu_info.get("Architecture", "Unknown"),
            "vendor": cpu_info.get("Vendor ID", "Unknown")
        }
        
        # 获取GPU信息
        print("正在获取GPU信息...")
        stdin, stdout, stderr = ssh.exec_command("nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader")
        gpu_output = stdout.read().decode("utf-8")
        gpu_error = stderr.read().decode("utf-8")
        
        if gpu_error:
            print(f"获取GPU信息时出错: {gpu_error}")
        
        # 解析GPU信息
        gpus = []
        for line in gpu_output.strip().split("\n"):
            if not line.strip():
                continue
                
            parts = line.split(", ")
            if len(parts) >= 3:
                index = parts[0].strip()
                name = parts[1].strip()
                memory = parts[2].strip()
                driver_version = parts[3].strip() if len(parts) > 3 else "Unknown"
                
                # 提取内存大小（去除MiB或MB后缀）
                memory_match = re.search(r'(\d+)', memory)
                memory_total = int(memory_match.group(1)) if memory_match else 0
                
                # 创建GPU信息
                gpu = {
                    "index": index,
                    "name": name,
                    "memory_total": memory_total,
                    "driver_version": driver_version
                }
                gpus.append(gpu)
        
        system_info["gpus"] = gpus
        
        # 获取主机名和操作系统信息
        stdin, stdout, stderr = ssh.exec_command("hostname")
        hostname = stdout.read().decode("utf-8").strip()
        system_info["hostname"] = hostname
        
        stdin, stdout, stderr = ssh.exec_command("uname -a")
        os_info = stdout.read().decode("utf-8").strip()
        system_info["os"] = os_info.split()[0]
        system_info["os_version"] = " ".join(os_info.split()[2:])
        
        return system_info
        
    except Exception as e:
        print(f"获取系统信息时出错: {e}")
        return None
    finally:
        ssh.close()

def update_cluster_node(cluster_id, node_id, system_info, center_controller_url):
    """更新集群节点信息"""
    try:
        # 构建更新请求
        update_data = {
            "node_id": node_id,
            "memory_total": system_info.get("memory_total", 0),
            "memory_available": system_info.get("memory_available", 0),
            "cpu_info": system_info.get("cpu_info", {}),
            "metadata": {
                "hostname": system_info.get("hostname", ""),
                "os": system_info.get("os", ""),
                "os_version": system_info.get("os_version", "")
            }
        }
        
        # 发送更新请求
        response = requests.post(
            f"{center_controller_url}/api/clusters/{cluster_id}/update_node",
            json=update_data
        )
        
        if response.status_code == 200:
            print(f"成功更新节点信息: {response.json()}")
            return True
        else:
            print(f"更新节点信息失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"更新节点信息时出错: {e}")
        return False

def main():
    # 集群ID
    cluster_id = "2d8204c7-3dbb-42ce-bbc2-81d4570f0f97"
    
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
    
    # 获取节点ID
    if not cluster_info.get("nodes"):
        print("集群中没有节点")
        return
    
    node_id = cluster_info["nodes"][0]["id"]
    print(f"节点ID: {node_id}")
    
    # 获取系统信息
    system_info = get_system_info(hostname, port, username, password)
    if not system_info:
        print("获取系统信息失败")
        return
    
    print(f"系统信息: {json.dumps(system_info, indent=2, ensure_ascii=False)}")
    
    # 更新节点信息
    update_cluster_node(cluster_id, node_id, system_info, center_controller_url)

if __name__ == "__main__":
    main()
