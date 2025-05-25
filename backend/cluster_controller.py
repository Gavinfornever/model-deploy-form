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
import threading
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# 导入集群注册模块
from ClusterRegister import (
    ClusterInfo, NodeInfo, GPUInfo, GPUType, 
    ResourceRegistry, AppleGPUAdapter, NvidiaGPUAdapter
)

# GPU资源管理
class GPUResourceManager:
    """GPU资源管理器，负责跟踪GPU使用情况"""
    
    def __init__(self):
        self.gpu_usage = {}  # gpu_id -> {model_id, memory_used, status}
        
    def allocate_gpu(self, model_id, gpu_id, memory_required=0):
        """分配GPU资源给模型"""
        if gpu_id not in self.gpu_usage:
            self.gpu_usage[gpu_id] = {
                "model_id": model_id,
                "memory_used": memory_required,
                "status": "allocated",
                "allocated_time": time.time()
            }
            return True
        elif self.gpu_usage[gpu_id]["status"] == "free":
            self.gpu_usage[gpu_id] = {
                "model_id": model_id,
                "memory_used": memory_required,
                "status": "allocated",
                "allocated_time": time.time()
            }
            return True
        return False
    
    def release_gpu(self, gpu_id):
        """释放GPU资源"""
        if gpu_id in self.gpu_usage:
            self.gpu_usage[gpu_id]["status"] = "free"
            self.gpu_usage[gpu_id]["model_id"] = None
            self.gpu_usage[gpu_id]["memory_used"] = 0
            return True
        return False
    
    def get_gpu_status(self, gpu_id):
        """获取GPU使用状态"""
        return self.gpu_usage.get(gpu_id, {"status": "unknown"})
    
    def find_available_gpu(self, memory_required=0, gpu_type=None):
        """查找可用的GPU"""
        for gpu_id, usage in self.gpu_usage.items():
            if usage["status"] == "free" and usage.get("memory_total", 0) >= memory_required:
                if gpu_type is None or usage.get("gpu_type") == gpu_type:
                    return gpu_id
        return None
    
    def register_gpu(self, gpu_id, gpu_info):
        """注册GPU到资源管理器"""
        if gpu_id not in self.gpu_usage:
            self.gpu_usage[gpu_id] = {
                "model_id": None,
                "memory_used": 0,
                "status": "free",
                "memory_total": gpu_info.memory_total,
                "gpu_type": gpu_info.gpu_type.value,
                "gpu_name": gpu_info.name
            }
            return True
        return False
    
    def get_all_gpus(self):
        """获取所有GPU信息"""
        return self.gpu_usage

# 配置日志
def setup_logging(log_path=None):
    """设置日志配置"""
    # 初始化日志器
    logger = logging.getLogger("cluster_controller")
    logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    for handler in logger.handlers[:]: 
        logger.removeHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    # 如果提供了日志路径，添加文件处理器
    if log_path:
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_path}")
        except Exception as e:
            logger.error(f"Warning: Could not create log file at {log_path}: {e}")
    
    return logger

# 初始化日志器
logger = logging.getLogger("cluster_controller")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        
        # 将GPU资源注册到GPU资源管理器
        for gpu in gpus:
            logger.info(f"Registering GPU {gpu.id} ({gpu.name}) to resource manager")
            gpu_manager.register_gpu(gpu.id, gpu)
        
        # 获取系统信息
        node.metadata["os"] = platform.system()
        node.metadata["os_version"] = platform.version()
        node.metadata["hostname"] = platform.node()
        
        # 获取CPU信息
        if platform.system() == "Darwin":  # macOS
            try:
                # 获取CPU核心数
                cmd = "sysctl -n hw.ncpu"
                cpu_cores = subprocess.check_output(cmd, shell=True).decode().strip()
                node.metadata["cpu_cores"] = cpu_cores
                
                # 获取CPU型号
                cmd = "sysctl -n machdep.cpu.brand_string"
                cpu_model = subprocess.check_output(cmd, shell=True).decode().strip()
                node.metadata["cpu_model"] = cpu_model
                
                # 获取内存大小
                cmd = "sysctl -n hw.memsize"
                memory = int(subprocess.check_output(cmd, shell=True).decode().strip())
                node.metadata["memory_total"] = memory // (1024 * 1024)  # 转换为MB
                
            except Exception as e:
                logger.error(f"Error getting system info: {e}")
        elif platform.system() == "Linux":  # Linux
            try:
                # 获取CPU核心数
                cmd = "nproc"
                cpu_cores = subprocess.check_output(cmd, shell=True).decode().strip()
                node.metadata["cpu_cores"] = cpu_cores
                
                # 获取CPU型号
                cmd = "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2"
                cpu_model = subprocess.check_output(cmd, shell=True).decode().strip()
                node.metadata["cpu_model"] = cpu_model
                
                # 获取内存大小
                cmd = "grep MemTotal /proc/meminfo | awk '{print $2}'"
                memory_kb = int(subprocess.check_output(cmd, shell=True).decode().strip())
                node.metadata["memory_total"] = memory_kb // 1024  # 转换为MB
                
            except Exception as e:
                logger.error(f"Error getting system info on Linux: {e}")
        
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

# ====================== API服务器 ======================

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用CORS

# 全局变量，用于存储集群信息
cluster_info = {
    "cluster_id": "",
    "cluster_name": "",
    "adapter_type": "",
    "center_controller_url": "",
    "nodes": []
}

# 部署任务队列
deployment_tasks = []

# 模型实例列表
model_instances = []

# GPU资源管理器
gpu_manager = GPUResourceManager()

# 模型实例端点列表
model_endpoints = []

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "success",
        "message": "集群控制器运行正常",
        "cluster_info": cluster_info,
        "model_instances": model_instances,
        "timestamp": time.time()
    })

@app.route('/api/deploy', methods=['POST'])
def deploy_model():
    """部署模型接口"""
    try:
        data = request.json
        logger.info(f"接收到部署请求: {data}")
        
        if not data or 'model_name' not in data:
            return jsonify({"status": "error", "message": "Missing required field: model_name"}), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 检查是否指定GPU ID或GPU数量
        gpu_id = data.get("gpu_id", None)
        gpu_count = data.get("gpu_count", 1)  # 默认使用一个GPU
        
        # 如果指定了特定GPU ID
        if gpu_id:
            # 检查指定的GPU是否存在且可用
            gpu_status = gpu_manager.get_gpu_status(gpu_id)
            if gpu_status["status"] == "unknown":
                return jsonify({"status": "error", "message": f"GPU {gpu_id} not found"}), 404
            elif gpu_status["status"] != "free":
                return jsonify({
                    "status": "error", 
                    "message": f"GPU {gpu_id} is not available, current status: {gpu_status['status']}"
                }), 400
            gpu_ids = [gpu_id]  # 已指定的GPU ID
        else:
            # 根据GPU数量自动分配GPU
            memory_required = data.get("memory_required", 0)
            gpu_type = data.get("gpu_type", None)
            node_id = data.get("node_id", None)  # 指定节点ID
            
            logger.info(f"尝试分配 {gpu_count} 个GPU，每个需要内存 {memory_required}MB")
            
            # 分配多个GPU
            gpu_ids = []
            for _ in range(int(gpu_count)):
                available_gpu = gpu_manager.find_available_gpu(memory_required, gpu_type, node_id)
                if available_gpu:
                    gpu_ids.append(available_gpu)
                    logger.info(f"分配到GPU: {available_gpu}")
                else:
                    # 如果找不到足够的GPU，释放已分配的GPU
                    for g_id in gpu_ids:
                        gpu_manager.release_gpu(g_id)
                    return jsonify({"status": "error", "message": f"无法分配{gpu_count}个GPU，只找到{len(gpu_ids)}个可用GPU"}), 400
            
            # 使用第一个GPU作为主要GPU
            gpu_id = gpu_ids[0] if gpu_ids else None
        
        # 创建部署任务
        task = {
            "task_id": task_id,
            "model_name": data["model_name"],
            "model_type": data.get("model_type", "transformers"),
            "gpu_id": gpu_id,
            "status": "pending",
            "created_at": time.time(),
            "updated_at": time.time(),
            "result": None
        }
        
        # 添加到任务队列
        deployment_tasks.append(task)
        
        # 启动单独的线程处理部署任务
        threading.Thread(target=process_deployment_task, args=(task,)).start()
        
        return jsonify({
            "status": "success",
            "message": f"Deployment task created for model {data['model_name']} on GPU {gpu_id}",
            "task_id": task_id,
            "gpu_id": gpu_id
        })
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务列表"""
    return jsonify({
        "status": "success",
        "tasks": deployment_tasks
    })

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """获取特定任务的状态"""
    for task in deployment_tasks:
        if task["task_id"] == task_id:
            return jsonify({
                "status": "success",
                "task": task
            })
    
    return jsonify({"status": "error", "message": "任务不存在"}), 404

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取所有模型实例"""
    return jsonify({
        "status": "success",
        "models": model_instances
    })

@app.route('/api/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """获取特定模型实例"""
    for model in model_instances:
        if model["model_id"] == model_id:
            return jsonify({
                "status": "success",
                "model": model
            })
    
    return jsonify({"status": "error", "message": "模型不存在"}), 404

@app.route('/api/models', methods=['POST'])
def register_model():
    """注册模型实例"""
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "没有提供数据"}), 400
        
        # 验证必要字段
        required_fields = ["model_id", "model_name", "model_type", "endpoint"]
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"缺少必要字段: {field}"}), 400
        
        # 检查模型ID是否已存在
        for model in model_instances:
            if model["model_id"] == data["model_id"]:
                return jsonify({"status": "error", "message": "模型ID已存在"}), 400
        
        # 添加时间戳和状态
        model_data = {
            **data,
            "registered_at": time.time(),
            "status": "online"
        }
        
        # 添加到模型实例列表
        model_instances.append(model_data)
        
        # 如果模型端点不在列表中，添加到端点列表
        if data["endpoint"] not in model_endpoints:
            model_endpoints.append(data["endpoint"])
            # 提取模型实例的基础URL，用于轮询
            # 从端点URL中提取主机和端口
            parts = data["endpoint"].split('/')
            if len(parts) >= 3:
                host_port = parts[2]  # 得到如 'localhost:5010'
                model_info_url = f"http://{host_port}/api/model_instances_info"
                if model_info_url not in model_endpoints:
                    model_endpoints.append(model_info_url)
                    logger.info(f"添加模型实例信息轮询端点: {model_info_url}")
        
        logger.info(f"注册模型实例: {model_data['model_name']} (ID: {model_data['model_id']})")
        
        return jsonify({
            "status": "success",
            "message": "模型实例注册成功",
            "model": model_data
        })
    except Exception as e:
        logger.error(f"注册模型实例时出错: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/model_instances_info', methods=['GET'])
def get_model_instances_info():
    """获取模型实例信息接口，供中心控制器轮询"""
    try:
        return jsonify({
            "status": "success",
            "cluster_id": cluster_info["cluster_id"],
            "cluster_name": cluster_info["cluster_name"],
            "model_instances": model_instances,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"Error getting model instances info: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/gpus', methods=['GET'])
def get_gpus():
    """获取集群中的GPU资源信息"""
    try:
        gpu_info = gpu_manager.get_all_gpus()
        return jsonify({
            "status": "success",
            "cluster_id": cluster_info["cluster_id"],
            "cluster_name": cluster_info["cluster_name"],
            "gpus": gpu_info,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"Error getting GPU info: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/gpus/<gpu_id>', methods=['GET'])
def get_gpu(gpu_id):
    """获取特定GPU的信息"""
    try:
        gpu_status = gpu_manager.get_gpu_status(gpu_id)
        if gpu_status["status"] == "unknown":
            return jsonify({"status": "error", "message": f"GPU {gpu_id} not found"}), 404
            
        return jsonify({
            "status": "success",
            "gpu_id": gpu_id,
            "gpu_info": gpu_status,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"Error getting GPU info: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/gpus/<gpu_id>/allocate', methods=['POST'])
def allocate_gpu(gpu_id):
    """分配GPU资源给模型"""
    try:
        data = request.json
        if not data or 'model_id' not in data:
            return jsonify({"status": "error", "message": "Missing required field: model_id"}), 400
            
        model_id = data['model_id']
        memory_required = data.get('memory_required', 0)
        
        # 检查GPU是否可用
        gpu_status = gpu_manager.get_gpu_status(gpu_id)
        if gpu_status["status"] != "free":
            return jsonify({
                "status": "error", 
                "message": f"GPU {gpu_id} is not available, current status: {gpu_status['status']}"
            }), 400
            
        # 分配GPU
        success = gpu_manager.allocate_gpu(model_id, gpu_id, memory_required)
        if not success:
            return jsonify({"status": "error", "message": f"Failed to allocate GPU {gpu_id}"}), 500
            
        return jsonify({
            "status": "success",
            "message": f"GPU {gpu_id} allocated to model {model_id}",
            "gpu_id": gpu_id,
            "model_id": model_id,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"Error allocating GPU: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/gpus/<gpu_id>/release', methods=['POST'])
def release_gpu(gpu_id):
    """释放GPU资源"""
    try:
        # 释放GPU
        success = gpu_manager.release_gpu(gpu_id)
        if not success:
            return jsonify({"status": "error", "message": f"Failed to release GPU {gpu_id}"}), 500
            
        return jsonify({
            "status": "success",
            "message": f"GPU {gpu_id} released",
            "gpu_id": gpu_id,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"Error releasing GPU: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def process_deployment_task(task):
    """处理部署任务"""
    try:
        task_id = task["task_id"]
        model_name = task["model_name"]
        model_type = task.get("model_type", "transformers")
        deploy_command = task.get("deploy_command", None)  # 自定义部署命令
        
        # 获取GPU IDs（可能是单个或多个）
        gpu_ids = task.get("gpu_ids", [])
        primary_gpu_id = task.get("gpu_id")  # 主要GPU ID
        
        if primary_gpu_id and primary_gpu_id not in gpu_ids:
            gpu_ids.append(primary_gpu_id)
        
        if not gpu_ids:
            raise Exception("No GPUs specified for deployment")
            
        logger.info(f"开始处理部署任务 {task_id}, 模型: {model_name}, GPUs: {gpu_ids}")
        
        # 更新任务状态
        task["status"] = "processing"
        task["started_at"] = time.time()
        
        # 生成模型ID
        model_id = str(uuid.uuid4())
        
        # 分配所有GPU给模型
        allocated_gpus = []
        for gpu_id in gpu_ids:
            success = gpu_manager.allocate_gpu(model_id, gpu_id)
            if success:
                allocated_gpus.append(gpu_id)
                logger.info(f"GPU {gpu_id} 分配给模型 {model_id} 成功")
            else:
                # 如果有一个GPU分配失败，释放已分配的GPU
                for allocated_gpu in allocated_gpus:
                    gpu_manager.release_gpu(allocated_gpu)
                raise Exception(f"Failed to allocate GPU {gpu_id} for model {model_id}")
        
        # 使用第一个GPU作为主要GPU
        primary_gpu = allocated_gpus[0] if allocated_gpus else None
        
        # 启动模型实例
        port = 5010 + int(time.time()) % 1000  # 生成一个不太可能冲突的端口
        
        # 使用自定义部署命令或生成默认命令
        if deploy_command:
            cmd = deploy_command
        else:
            # 构建启动命令，包含所有GPU IDs
            gpu_args = ",".join(allocated_gpus)
            cmd = f"python start_qwen_model.py --model-name \"{model_name}\" --port {port} --cluster-controller \"http://localhost:{cluster_info.get('port', 5010)}\" --gpu-ids {gpu_args}"
        
        logger.info(f"启动模型实例: {cmd}")
        
        # 在实际环境中执行部署命令
        try:
            # 使用subprocess执行命令，非阻塞模式
            import subprocess
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            logger.info(f"模型部署进程启动，PID: {process.pid}")
        except Exception as e:
            # 如果启动失败，释放所有GPU
            for gpu_id in allocated_gpus:
                gpu_manager.release_gpu(gpu_id)
            raise Exception(f"Failed to start model process: {e}")
        
        # 创建模型实例记录
        model_instance = {
            "model_id": model_id,
            "model_name": model_name,
            "model_type": model_type,
            "gpu_ids": allocated_gpus,  # 所有分配的GPU
            "primary_gpu": primary_gpu,  # 主要GPU
            "endpoint": f"http://localhost:{port}/api/generate",
            "status": "starting",  # 初始状态为启动中
            "created_at": time.time(),
            "node_id": task.get("node_id") or (cluster_info["nodes"][0]["id"] if cluster_info.get("nodes") else None),
            "process_id": process.pid
        }
        
        # 添加到模型实例列表
        model_instances.append(model_instance)
        
        # 更新任务结果
        task["result"] = {
            "model_id": model_id,
            "endpoint": model_instance["endpoint"],
            "gpu_ids": allocated_gpus,
            "primary_gpu": primary_gpu
        }
        
        # 更新任务状态为完成
        task["status"] = "completed"
        task["completed_at"] = time.time()
        logger.info(f"部署任务 {task_id} 完成, 模型实例已启动")
    except Exception as e:
        logger.error(f"处理部署任务 {task['task_id']} 时出错: {e}")
        task["status"] = "failed"
        task["error"] = str(e)
        
        # 如果失败，释放GPU资源
        if "gpu_id" in task:
            gpu_manager.release_gpu(task["gpu_id"])
        task["failed_at"] = time.time()

def poll_model_instances():
    """轮询模型实例信息的线程"""
    global model_instances, model_endpoints
    
    # 记录端点失败次数
    endpoint_failures = {}
    # 失败次数阈值，超过该阈值则将模型实例标记为离线
    max_failures = 3
    
    while True:
        try:
            # 逐个轮询模型实例端点
            for endpoint in list(model_endpoints):  # 使用副本避免循环中修改
                try:
                    # 只轮询model_instances_info端点
                    if not endpoint.endswith('/api/model_instances_info'):
                        continue
                        
                    logger.debug(f"轮询模型实例信息: {endpoint}")
                    response = requests.get(endpoint, timeout=3)
                    
                    if response.status_code == 200:
                        # 重置失败计数
                        endpoint_failures[endpoint] = 0
                        
                        data = response.json()
                        if data.get("status") == "success" and "model_instances" in data:
                            # 更新模型实例信息
                            for instance in data["model_instances"]:
                                # 检查模型ID是否已存在
                                found = False
                                for i, model in enumerate(model_instances):
                                    if model["model_id"] == instance["model_id"]:
                                        # 更新现有模型实例信息
                                        model_instances[i] = instance
                                        # 确保状态为在线
                                        model_instances[i]["status"] = "online"
                                        found = True
                                        break
                                        
                                if not found:
                                    # 添加新的模型实例
                                    instance["status"] = "online"  # 确保状态为在线
                                    model_instances.append(instance)
                                    logger.info(f"发现新模型实例: {instance.get('model_name', 'unknown')} (ID: {instance.get('model_id', 'unknown')})")
                    else:
                        # 增加失败计数
                        endpoint_failures[endpoint] = endpoint_failures.get(endpoint, 0) + 1
                        logger.warning(f"轮询模型实例失败: {endpoint}, 状态码: {response.status_code}, 失败次数: {endpoint_failures[endpoint]}")
                        
                        # 检查是否超过失败阈值
                        if endpoint_failures[endpoint] >= max_failures:
                            # 从端点URL提取主机和端口
                            parts = endpoint.split('/')
                            if len(parts) >= 3:
                                host_port = parts[2]  # 如 'localhost:5010'
                                # 将相关模型实例标记为离线
                                for i, model in enumerate(model_instances):
                                    if model["endpoint"].startswith(f"http://{host_port}"):
                                        model_instances[i]["status"] = "offline"
                                        logger.warning(f"模型实例标记为离线: {model['model_name']} (ID: {model['model_id']})")
                        
                except requests.RequestException as e:
                    # 增加失败计数
                    endpoint_failures[endpoint] = endpoint_failures.get(endpoint, 0) + 1
                    logger.warning(f"轮询模型实例时出错: {endpoint}, 错误: {e}, 失败次数: {endpoint_failures[endpoint]}")
                    
                    # 检查是否超过失败阈值
                    if endpoint_failures[endpoint] >= max_failures:
                        # 从端点URL提取主机和端口
                        parts = endpoint.split('/')
                        if len(parts) >= 3:
                            host_port = parts[2]  # 如 'localhost:5010'
                            # 将相关模型实例标记为离线
                            for i, model in enumerate(model_instances):
                                if model["endpoint"].startswith(f"http://{host_port}"):
                                    model_instances[i]["status"] = "offline"
                                    logger.warning(f"模型实例标记为离线: {model['model_name']} (ID: {model['model_id']})")
            
            # 每5秒轮询一次
            time.sleep(5)
        except Exception as e:
            logger.error(f"模型实例轮询线程出错: {e}")
            time.sleep(10)  # 出错后等待10秒再重试

def heartbeat_thread(nodes, center_controller_url, cluster_id):
    """心跳线程，定期向中心控制器发送节点状态"""
    while True:
        try:
            # 更新节点状态
            for node in nodes:
                node.last_heartbeat = time.time()
                node_dict = node_to_dict(node)
                register_with_center_controller(center_controller_url, cluster_id, node_dict)
            
            # 每60秒发送一次心跳
            time.sleep(60)
        except Exception as e:
            logger.error(f"心跳线程出错: {e}")
            time.sleep(10)  # 出错后等待10秒再重试

# ====================== 主函数 ======================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Cluster Controller")
    parser.add_argument("--config", required=True, help="Path to config file")
    parser.add_argument("--log-path", help="Path to log file")
    parser.add_argument("--port", type=int, default=5002, help="Port for the controller")
    args = parser.parse_args()
    
    # 设置日志
    global logger
    logger = setup_logging(args.log_path)
    
    # 记录启动信息
    logger.info("===== Cluster Controller Starting =====")
    logger.info(f"Command line arguments: {args}")
    if args.log_path:
        logger.info(f"Logging to: {args.log_path}")
        
    # 设置端口
    port = args.port
    logger.info(f"Will start API server on port {port}")
    
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
    
    # 更新全局集群信息
    global cluster_info
    cluster_info["cluster_id"] = cluster_id
    cluster_info["cluster_name"] = cluster_name
    cluster_info["adapter_type"] = adapter_type
    cluster_info["center_controller_url"] = center_controller_url
    cluster_info["nodes"] = [node_to_dict(node) for node in nodes]
    
    # 启动心跳线程
    heart_thread = threading.Thread(
        target=heartbeat_thread,
        args=(nodes, center_controller_url, cluster_id)
    )
    heart_thread.daemon = True
    heart_thread.start()
    logger.info("Started heartbeat thread")
    
    # 启动模型实例轮询线程
    poll_thread = threading.Thread(
        target=poll_model_instances
    )
    poll_thread.daemon = True
    poll_thread.start()
    logger.info("Started model instances polling thread")
    
    # 启动Flask服务器
    logger.info(f"Starting API server on port {port}")
    try:
        # 确保端口是整数
        if isinstance(port, str):
            port = int(port)
        
        # 使用更稳定的方式启动Flask
        from werkzeug.serving import run_simple
        logger.info(f"Starting server with port {port} (type: {type(port).__name__})")
        run_simple('0.0.0.0', port, app, threaded=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        
        # 尝试使用备用端口
        backup_port = 5020
        logger.info(f"Trying backup port: {backup_port}")
        try:
            run_simple('0.0.0.0', backup_port, app, threaded=True, use_reloader=False)
        except Exception as e2:
            logger.error(f"Failed to start API server with backup port: {e2}")
            logger.error("Could not start API server. Continuing with heartbeat only.")
            
            # 如果服务器启动失败，但心跳线程已启动，保持程序运行
            while True:
                try:
                    time.sleep(60)
                except KeyboardInterrupt:
                    logger.info("Stopping cluster controller")
                    break

if __name__ == "__main__":
    main()
