#!/usr/bin/env python3
"""
集群控制器 (Cluster Controller)
部署在集群的中心节点上，负责发现节点和资源，并将信息注册到中心控制器
"""

import json
import os
import time
import uuid
import logging
import argparse
import requests
import platform
import subprocess
from typing import Dict, List, Any, Optional

# 导入集群注册模块
from ClusterRegister import (
    ClusterInfo, NodeInfo, GPUInfo, GPUType, 
    ResourceRegistry, AppleGPUAdapter, NvidiaGPUAdapter
)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cluster_controller")

# ====================== 辅助函数 ======================

def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def discover_local_resources(adapter_type: str) -> List[NodeInfo]:
    """发现本地资源"""
    logger.info(f"Discovering local resources using adapter type: {adapter_type}")
    
    # 初始化资源注册中心
    registry = ResourceRegistry()
    
    # 注册适配器
    if adapter_type == "apple":
        registry.register_adapter(AppleGPUAdapter())
    elif adapter_type == "nvidia":
        registry.register_adapter(NvidiaGPUAdapter())
    else:
        logger.error(f"Unsupported adapter type: {adapter_type}")
        return []
    
    # 创建适配器配置
    adapter_config = {
        "nodes": [
            {
                "id": str(uuid.uuid4()),
                "name": platform.node(),
                "ip": "127.0.0.1",
                "port": 22
            }
        ]
    }
    
    # 使用适配器发现节点
    adapter = registry.adapters.get(adapter_type)
    if not adapter:
        logger.error(f"Adapter not found: {adapter_type}")
        return []
    
    nodes = adapter.discover_nodes(adapter_config)
    
    # 获取每个节点的GPU信息
    for node in nodes:
        gpus = adapter.get_gpu_info(node)
        node.gpus = gpus
        node.status = "online"
        node.last_heartbeat = time.time()
        
        # 获取系统信息
        node.metadata["os"] = platform.system()
        node.metadata["os_version"] = platform.version()
        node.metadata["hostname"] = platform.node()
        
        # 获取CPU和内存信息
        try:
            if platform.system() == "Darwin":  # macOS
                # 获取CPU信息
                cmd = "sysctl -n hw.ncpu"
                cpu_cores = int(subprocess.check_output(cmd, shell=True).decode().strip())
                
                cmd = "sysctl -n machdep.cpu.brand_string"
                cpu_model = subprocess.check_output(cmd, shell=True).decode().strip()
                
                # 获取CPU架构
                cmd = "uname -m"
                cpu_arch = subprocess.check_output(cmd, shell=True).decode().strip()
                
                # 获取CPU厂商
                cmd = "sysctl -n machdep.cpu.vendor"
                cpu_vendor = subprocess.check_output(cmd, shell=True).decode().strip()
                
                # 创建CPU信息字典
                node.cpu_info = {
                    "model": cpu_model,
                    "cores": cpu_cores,
                    "architecture": cpu_arch,
                    "vendor": cpu_vendor
                }
                
                # 获取内存大小
                cmd = "sysctl -n hw.memsize"
                memory_total = int(subprocess.check_output(cmd, shell=True).decode().strip())
                node.memory_total = memory_total // (1024 * 1024)  # 转换为MB
                
                # 获取可用内存
                cmd = "vm_stat | grep 'Pages free' | awk '{print $3}' | sed 's/\\.//'" 
                pages_free = int(subprocess.check_output(cmd, shell=True).decode().strip())
                page_size = int(subprocess.check_output("sysctl -n hw.pagesize", shell=True).decode().strip())
                memory_available = (pages_free * page_size) // (1024 * 1024)  # 转换为MB
                node.memory_available = memory_available
                
            elif platform.system() == "Linux":  # Linux
                # 获取CPU信息
                cmd = "nproc"
                cpu_cores = int(subprocess.check_output(cmd, shell=True).decode().strip())
                
                cmd = "cat /proc/cpuinfo | grep 'model name' | head -n 1 | cut -d ':' -f 2"
                cpu_model = subprocess.check_output(cmd, shell=True).decode().strip()
                
                # 获取CPU架构
                cmd = "uname -m"
                cpu_arch = subprocess.check_output(cmd, shell=True).decode().strip()
                
                # 获取CPU厂商
                cmd = "cat /proc/cpuinfo | grep 'vendor_id' | head -n 1 | cut -d ':' -f 2"
                cpu_vendor = subprocess.check_output(cmd, shell=True).decode().strip()
                
                # 创建CPU信息字典
                node.cpu_info = {
                    "model": cpu_model,
                    "cores": cpu_cores,
                    "architecture": cpu_arch,
                    "vendor": cpu_vendor
                }
                
                # 获取内存信息
                cmd = "free -m | grep Mem | awk '{print $2}'"
                memory_total = int(subprocess.check_output(cmd, shell=True).decode().strip())
                node.memory_total = memory_total
                
                cmd = "free -m | grep Mem | awk '{print $7}'"
                memory_available = int(subprocess.check_output(cmd, shell=True).decode().strip())
                node.memory_available = memory_available
            
            # 同时保留在metadata中，以保持兼容性
            node.metadata["cpu_model"] = node.cpu_info["model"]
            node.metadata["cpu_cores"] = node.cpu_info["cores"]
            node.metadata["memory_total"] = node.memory_total
            node.metadata["memory_available"] = node.memory_available
                
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
        
        logger.info(f"Discovered node: {node.name} with {len(node.gpus)} GPUs")
        
    return nodes

def register_with_center_controller(center_url: str, cluster_id: str, node_info: Dict[str, Any]) -> bool:
    """向中心控制器注册节点信息"""
    try:
        url = f"{center_url}/api/register_node"
        payload = {
            "cluster_id": cluster_id,
            "node_info": node_info
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                logger.info("Successfully registered with center controller")
                return True
            else:
                logger.error(f"Registration failed: {result.get('message')}")
                return False
        else:
            logger.error(f"Registration failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error registering with center controller: {e}")
        return False

def node_to_dict(node: NodeInfo) -> Dict[str, Any]:
    """将NodeInfo对象转换为字典"""
    node_dict = {
        "id": node.id,
        "name": node.name,
        "ip": node.ip,
        "port": node.port,
        "status": node.status,
        "last_heartbeat": node.last_heartbeat,
        "metadata": node.metadata,
        "gpus": []
    }
    
    # 添加内存信息
    if hasattr(node, 'memory_total') and node.memory_total > 0:
        node_dict["memory_total"] = node.memory_total
    if hasattr(node, 'memory_available') and node.memory_available > 0:
        node_dict["memory_available"] = node.memory_available
    
    # 添加CPU信息
    if hasattr(node, 'cpu_info') and node.cpu_info:
        node_dict["cpu_info"] = node.cpu_info
    
    # 添加GPU信息
    for gpu in node.gpus:
        gpu_dict = {
            "id": gpu.id,
            "name": gpu.name,
            "memory_total": gpu.memory_total,
            "gpu_type": gpu.gpu_type.value,
            "compute_capability": gpu.compute_capability,
            "extra_info": gpu.extra_info
        }
        node_dict["gpus"].append(gpu_dict)
        
    return node_dict

def discover_additional_nodes() -> List[NodeInfo]:
    """
    发现集群中的其他节点
    
    在实际环境中，这里会使用网络发现或配置文件来查找其他节点
    对于演示目的，我们模拟发现一些额外的节点
    """
    # 这里只是演示，实际实现会根据网络发现或配置文件查找节点
    return []

# ====================== 主函数 ======================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Cluster Controller")
    parser.add_argument("--config", required=True, help="Path to config file")
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    if not config:
        logger.error("Failed to load config")
        return
    
    # 获取配置信息
    cluster_id = config.get("cluster_id")
    cluster_name = config.get("cluster_name")
    adapter_type = config.get("adapter_type")
    center_controller_url = config.get("center_controller_url")
    logger.info(center_controller_url)
    logger.info(center_controller_url)
    logger.info(center_controller_url)
    logger.info(center_controller_url)
    
    if not all([cluster_id, cluster_name, adapter_type, center_controller_url]):
        logger.error("Missing required config")
        return
    
    logger.info(f"Starting cluster controller for cluster: {cluster_name}")
    
    # 发现本地资源
    nodes = discover_local_resources(adapter_type)
    
    if not nodes:
        logger.error("No nodes discovered")
        return
    
    # 发现其他节点
    additional_nodes = discover_additional_nodes()
    nodes.extend(additional_nodes)
    
    # 注册到中心控制器
    for node in nodes:
        node_dict = node_to_dict(node)
        success = register_with_center_controller(center_controller_url, cluster_id, node_dict)
        
        if success:
            logger.info(f"Node {node.name} registered successfully")
        else:
            logger.error(f"Failed to register node {node.name}")
    
    # 启动心跳线程
    while True:
        try:
            # 更新节点状态
            for node in nodes:
                node.last_heartbeat = time.time()
                node_dict = node_to_dict(node)
                register_with_center_controller(center_controller_url, cluster_id, node_dict)
            
            # 每60秒发送一次心跳
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("Stopping cluster controller")
            break
        except Exception as e:
            logger.error(f"Error in heartbeat: {e}")
            time.sleep(10)  # 出错后等待10秒再重试

if __name__ == "__main__":
    main()
