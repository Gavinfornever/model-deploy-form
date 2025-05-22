#!/usr/bin/env python3
"""
中心控制器 (Center Controller)
替代原API Server，管理集群注册和资源发现
"""

import json
import os
import time
import uuid
import logging
import redis
import paramiko
from paramiko import SSHClient
from scp import SCPClient
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from typing import Dict, List, Any, Optional

# 导入集群注册模块
from ClusterRegister import (
    ClusterInfo, NodeInfo, GPUInfo, GPUType, 
    ResourceRegistry, AppleGPUAdapter, NvidiaGPUAdapter
)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("center_controller")

# 初始化Flask应用
app = Flask(__name__)
CORS(app)

# 配置JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 24 * 60 * 60  # 1天
jwt = JWTManager(app)

# 配置Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# 初始化Redis连接
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# 初始化资源注册中心
resource_registry = ResourceRegistry()

# 注册适配器
resource_registry.register_adapter(AppleGPUAdapter())
resource_registry.register_adapter(NvidiaGPUAdapter())

# 集群控制器代码路径
CLUSTER_CONTROLLER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    "cluster_controller.py"
)

# ====================== 辅助函数 ======================

def save_cluster_to_redis(cluster: ClusterInfo):
    """将集群信息保存到Redis"""
    # 将集群对象转换为字典
    cluster_dict = {
        "id": cluster.id,
        "name": cluster.name,
        "adapter_type": cluster.adapter_type,
        "config": cluster.config,
        "nodes": []
    }
    
    # 添加节点信息
    for node in cluster.nodes:
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
            
        cluster_dict["nodes"].append(node_dict)
    
    # 保存到Redis
    redis_client.hset("clusters", cluster.id, json.dumps(cluster_dict))
    logger.info(f"Saved cluster {cluster.name} to Redis")

def load_clusters_from_redis():
    """从Redis加载所有集群信息"""
    clusters = []
    
    # 获取所有集群
    all_clusters = redis_client.hgetall("clusters")
    
    for cluster_id, cluster_json in all_clusters.items():
        cluster_dict = json.loads(cluster_json)
        
        # 创建集群对象
        cluster = ClusterInfo(
            id=cluster_dict["id"],
            name=cluster_dict["name"],
            adapter_type=cluster_dict["adapter_type"],
            config=cluster_dict["config"],
            nodes=[]
        )
        
        # 添加节点
        for node_dict in cluster_dict["nodes"]:
            node = NodeInfo(
                id=node_dict["id"],
                name=node_dict["name"],
                ip=node_dict["ip"],
                port=node_dict["port"],
                status=node_dict["status"],
                last_heartbeat=node_dict["last_heartbeat"],
                metadata=node_dict["metadata"],
                gpus=[]
            )
            
            # 添加GPU
            for gpu_dict in node_dict["gpus"]:
                gpu = GPUInfo(
                    id=gpu_dict["id"],
                    name=gpu_dict["name"],
                    memory_total=gpu_dict["memory_total"],
                    gpu_type=GPUType(gpu_dict["gpu_type"]),
                    compute_capability=gpu_dict["compute_capability"],
                    extra_info=gpu_dict["extra_info"]
                )
                node.gpus.append(gpu)
                
            cluster.nodes.append(node)
            
        clusters.append(cluster)
    
    return clusters

def deploy_cluster_controller(cluster_info: Dict[str, Any]):
    """
    部署集群控制器到远程节点
    
    Args:
        cluster_info: 包含集群信息的字典
    
    Returns:
        成功部署返回True，否则返回False
    """
    try:
        # 检查是否是本地环境
        center_node_ip = cluster_info["center_node_ip"]
        is_local = center_node_ip in ["127.0.0.1", "localhost"]
        
        # 获取当前机器的IP地址，用于远程连接回中心控制器
        import socket
        local_ip = None
        try:
            # 尝试获取当前机器的外部IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            logger.info(f"Detected local IP: {local_ip}")
        except:
            # 如果无法获取外部IP，使用本地IP
            local_ip = "127.0.0.1"
            logger.warning(f"Could not detect external IP, using {local_ip}")
        
        # 创建配置文件
        config = {
            "cluster_id": cluster_info["id"],
            "cluster_name": cluster_info["name"],
            "adapter_type": cluster_info["adapter_type"],
            "center_controller_url": cluster_info.get("center_controller_url", f"http://{local_ip}:5001" if not is_local else "http://localhost:5001"),
            "center_node_ip": center_node_ip,
            "center_node_port": int(cluster_info.get("center_node_port", 22)),
            "nodes": [{
                "id": str(uuid.uuid4()),
                "name": f"node-{center_node_ip}",
                "ip": center_node_ip,  # 始终使用实际的远程IP地址
                "port": int(cluster_info.get("center_node_port", 22)),
                "metadata": {
                    "username": cluster_info.get("username", ""),
                    "password": cluster_info.get("password", "")
                }
            }]
        }
        logger.info(f"Using center controller URL: {config['center_controller_url']}")
        
        # 如果是本地环境，直接运行集群控制器
        if is_local:
            logger.info("Deploying cluster controller locally")
            
            # 创建配置文件
            config_path = "/tmp/cluster_config.json"
            with open(config_path, "w") as f:
                json.dump(config, f)
            
            # 直接导入集群控制器模块并运行
            import importlib.util
            import sys
            import subprocess
            import threading
            
            try:
                # 动态加载模块
                spec = importlib.util.spec_from_file_location("cluster_controller", CLUSTER_CONTROLLER_PATH)
                cluster_controller = importlib.util.module_from_spec(spec)
                sys.modules["cluster_controller"] = cluster_controller
                spec.loader.exec_module(cluster_controller)
                
                # 启动一个线程来运行集群控制器
                def run_controller():
                    # 设置命令行参数
                    sys.argv = [CLUSTER_CONTROLLER_PATH, "--config", config_path]
                    # 运行主函数
                    cluster_controller.main()
                
                # 启动线程
                thread = threading.Thread(target=run_controller)
                thread.daemon = True  # 设置为后台线程
                thread.start()
                
                # 模拟进程对象
                class DummyProcess:
                    def poll(self):
                        return None if thread.is_alive() else 1
                    
                    def communicate(self):
                        return b"", b""
                
                process = DummyProcess()
                
                # 等待一小段时间，检查是否启动成功
                time.sleep(2)
                if thread.is_alive():
                    logger.info("Successfully started local cluster controller")
                    return True, ""
                else:
                    error_message = "Failed to start local cluster controller"
                    logger.error(error_message)
                    return False, error_message
                    
            except Exception as e:
                logger.error(f"Error starting local cluster controller: {e}")
                return False, str(e)
        
        # 如果是远程环境，使用SSH部署
        else:
            center_node_port = int(cluster_info.get("center_node_port", 22))
            username = cluster_info.get("username", "root")
            password = cluster_info.get("password")
            key_path = cluster_info.get("key_path")
            
            logger.info(f"Deploying cluster controller to {center_node_ip}:{center_node_port} as {username}")
            
            # 创建SSH客户端
            ssh = SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接到远程服务器
            try:
                if key_path:
                    logger.info(f"Connecting using key file: {key_path}")
                    ssh.connect(
                        center_node_ip, 
                        port=center_node_port, 
                        username=username, 
                        key_filename=key_path,
                        timeout=10
                    )
                else:
                    logger.info("Connecting using password")
                    ssh.connect(
                        center_node_ip, 
                        port=center_node_port, 
                        username=username, 
                        password=password,
                        timeout=10
                    )
                
                logger.info(f"Successfully connected to {center_node_ip}")
            except Exception as e:
                logger.error(f"Failed to connect to {center_node_ip}: {e}")
                return False, f"Failed to connect to {center_node_ip}: {e}"
            
            try:
                # 创建SCP客户端
                scp = SCPClient(ssh.get_transport())
                
                # 上传集群控制器代码
                remote_path = "/tmp/cluster_controller.py"
                scp.put(CLUSTER_CONTROLLER_PATH, remote_path)
                logger.info(f"Uploaded cluster controller to {remote_path}")
                
                # 上传ClusterRegister.py
                cluster_register_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    "ClusterRegister.py"
                )
                scp.put(cluster_register_path, "/tmp/ClusterRegister.py")
                logger.info(f"Uploaded ClusterRegister.py to /tmp/ClusterRegister.py")
                
                # 上传requirements.txt
                requirements_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), 
                    "requirements.txt"
                )
                scp.put(requirements_path, "/tmp/requirements.txt")
                logger.info(f"Uploaded requirements.txt to /tmp/requirements.txt")
                
                # 创建配置文件
                config_path = "/tmp/cluster_config.json"
                with open("/tmp/cluster_config.json", "w") as f:
                    json.dump(config, f)
                
                scp.put("/tmp/cluster_config.json", config_path)
                logger.info(f"Uploaded configuration to {config_path}")
                
                # 安装依赖
                logger.info("Installing dependencies on remote server...")
                cmd = "cd /tmp && pip install -r requirements.txt"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error = stderr.read().decode()
                    logger.warning(f"Dependency installation warning: {error}")
                else:
                    logger.info("Dependencies installed successfully")
                
                # 停止可能正在运行的集群控制器
                cmd = "pkill -f cluster_controller.py || echo 'No existing cluster controller process found'"
                ssh.exec_command(cmd)
                logger.info("Stopped any existing cluster controller processes")
                
                # 启动集群控制器
                cmd = f"cd /tmp && nohup python3 cluster_controller.py --config {config_path} > cluster_controller.log 2>&1 &"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status == 0:
                    logger.info(f"Successfully started cluster controller on {center_node_ip}")
                    
                    # 检查是否成功启动
                    time.sleep(2)  # 等待一下让进程启动
                    cmd = "ps aux | grep cluster_controller.py | grep -v grep"
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    output = stdout.read().decode()
                    
                    if output.strip():
                        logger.info("Verified cluster controller is running")
                        # 查看日志
                        cmd = "tail -n 20 /tmp/cluster_controller.log"
                        stdin, stdout, stderr = ssh.exec_command(cmd)
                        log_output = stdout.read().decode()
                        logger.info(f"Cluster controller log:\n{log_output}")
                        return True, ""
                    else:
                        error_message = "Cluster controller process not found after starting"
                        logger.error(error_message)
                        return False, error_message
                else:
                    error = stderr.read().decode()
                    error_message = f"Failed to start cluster controller: {error}"
                    logger.error(error_message)
                    return False, error_message
            except Exception as e:
                logger.error(f"Error during deployment: {e}")
                return False, f"Error during deployment: {e}"
            finally:
                # 关闭SSH连接
                ssh.close()
            
    except Exception as e:
        error_message = f"Error deploying cluster controller: {e}"
        logger.error(error_message)
        return False, error_message

# ====================== API路由 ======================

@app.route('/api/clusters/<cluster_id>/update_node', methods=['POST'])
def update_node_info(cluster_id):
    """
    更新节点信息 API
    允许更新节点的内存、CPU和元数据信息
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
            
        # 验证必要字段
        required_fields = ["node_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        node_id = data["node_id"]
        
        # 从 Redis 获取集群信息
        cluster_json = redis_client.hget("clusters", cluster_id)
        
        if not cluster_json:
            return jsonify({
                "status": "error",
                "message": "Cluster not found"
            }), 404
            
        cluster_dict = json.loads(cluster_json)
        
        # 查找节点
        node_found = False
        for i, node in enumerate(cluster_dict["nodes"]):
            if node["id"] == node_id:
                # 更新节点信息
                if "memory_total" in data:
                    node["memory_total"] = data["memory_total"]
                if "memory_available" in data:
                    node["memory_available"] = data["memory_available"]
                if "cpu_info" in data:
                    node["cpu_info"] = data["cpu_info"]
                if "metadata" in data:
                    # 合并元数据，而不是完全替换
                    if "metadata" not in node:
                        node["metadata"] = {}
                    node["metadata"].update(data["metadata"])
                
                node_found = True
                break
                
        if not node_found:
            return jsonify({
                "status": "error",
                "message": "Node not found in cluster"
            }), 404
            
        # 更新 Redis
        redis_client.hset("clusters", cluster_id, json.dumps(cluster_dict))
        
        return jsonify({
            "status": "success",
            "message": "Node information updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating node info: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/clusters', methods=['GET'])
# @jwt_required()
def get_clusters():
    """获取所有集群信息"""
    try:
        clusters = load_clusters_from_redis()
        
        # 转换为JSON格式
        cluster_list = []
        for cluster in clusters:
            cluster_dict = {
                "id": cluster.id,
                "name": cluster.name,
                "adapter_type": cluster.adapter_type,
                "nodes_count": len(cluster.nodes),
                "gpus_count": sum(len(node.gpus) for node in cluster.nodes),
                "status": "online" if any(node.status == "online" for node in cluster.nodes) else "offline"
            }
            cluster_list.append(cluster_dict)
            
        return jsonify({
            "status": "success",
            "data": cluster_list
        })
        
    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/clusters/<cluster_id>', methods=['GET'])
# @jwt_required()
def get_cluster(cluster_id):
    """获取特定集群的详细信息"""
    try:
        # 从Redis获取集群信息
        cluster_json = redis_client.hget("clusters", cluster_id)
        
        if not cluster_json:
            return jsonify({
                "status": "error",
                "message": "Cluster not found"
            }), 404
            
        cluster_dict = json.loads(cluster_json)
        return jsonify({
            "status": "success",
            "data": cluster_dict
        })
        
    except Exception as e:
        logger.error(f"Error getting cluster {cluster_id}: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/clusters', methods=['POST'])
# @jwt_required()
def register_cluster():
    """注册新集群"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
            
        # 验证必要字段
        required_fields = ["name", "adapter_type", "center_node_ip", "center_controller_url"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # 如果是远程服务器，验证连接信息
        center_node_ip = data["center_node_ip"]
        is_local = center_node_ip in ["127.0.0.1", "localhost"]
        
        if not is_local:
            # 验证远程连接信息
            if "username" not in data:
                return jsonify({
                    "status": "error",
                    "message": "Username is required for remote deployment"
                }), 400
            
            # 验证认证方式
            if "password" not in data and "key_path" not in data:
                return jsonify({
                    "status": "error",
                    "message": "Either password or key_path is required for remote deployment"
                }), 400
                
        # 创建集群ID
        cluster_id = str(uuid.uuid4())
        
        # 创建集群对象
        cluster = ClusterInfo(
            id=cluster_id,
            name=data["name"],
            adapter_type=data["adapter_type"],
            config={
                "center_controller_url": data["center_controller_url"],
                "center_node_ip": data["center_node_ip"]
            },
            nodes=[]
        )
        
        # 保存到Redis
        save_cluster_to_redis(cluster)
        
        # 部署集群控制器
        data["id"] = cluster_id
        success, error_message = deploy_cluster_controller(data)
        
        if not success:
            # 如果部署失败，删除集群
            redis_client.hdel("clusters", cluster_id)
            
            return jsonify({
                "status": "error",
                "message": f"Failed to deploy cluster controller: {error_message}"
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "Cluster registration initiated",
            "data": {
                "cluster_id": cluster_id,
                "name": data["name"]
            }
        })
        
    except Exception as e:
        logger.error(f"Error registering cluster: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/clusters/<cluster_id>', methods=['DELETE'])
# @jwt_required()
def delete_cluster(cluster_id):
    """删除集群"""
    try:
        # 检查集群是否存在
        cluster_json = redis_client.hget("clusters", cluster_id)
        
        if not cluster_json:
            return jsonify({
                "status": "error",
                "message": "Cluster not found"
            }), 404
            
        # 从Redis删除集群
        redis_client.hdel("clusters", cluster_id)
        
        return jsonify({
            "status": "success",
            "message": "Cluster deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting cluster {cluster_id}: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/clusters/<cluster_id>/nodes', methods=['GET'])
# @jwt_required()
def get_cluster_nodes(cluster_id):
    """获取集群中的所有节点"""
    try:
        # 从Redis获取集群信息
        cluster_json = redis_client.hget("clusters", cluster_id)
        
        if not cluster_json:
            return jsonify({
                "status": "error",
                "message": "Cluster not found"
            }), 404
            
        cluster_dict = json.loads(cluster_json)
        
        return jsonify({
            "status": "success",
            "data": cluster_dict["nodes"]
        })
        
    except Exception as e:
        logger.error(f"Error getting nodes for cluster {cluster_id}: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/register_node', methods=['POST'])
def register_node():
    """
    注册节点API - 由集群控制器调用
    不需要JWT认证，因为这是集群控制器调用的内部API
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
            
        # 验证必要字段
        required_fields = ["cluster_id", "node_info"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        cluster_id = data["cluster_id"]
        node_info = data["node_info"]
        
        # 从Redis获取集群信息
        cluster_json = redis_client.hget("clusters", cluster_id)
        
        if not cluster_json:
            return jsonify({
                "status": "error",
                "message": "Cluster not found"
            }), 404
            
        cluster_dict = json.loads(cluster_json)
        
        # 检查节点是否已存在
        node_exists = False
        for i, node in enumerate(cluster_dict["nodes"]):
            if node["id"] == node_info["id"]:
                # 更新节点信息
                cluster_dict["nodes"][i] = node_info
                node_exists = True
                break
                
        if not node_exists:
            # 添加新节点
            cluster_dict["nodes"].append(node_info)
            
        # 更新Redis
        redis_client.hset("clusters", cluster_id, json.dumps(cluster_dict))
        
        return jsonify({
            "status": "success",
            "message": "Node registered successfully"
        })
        
    except Exception as e:
        logger.error(f"Error registering node: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ====================== 主函数 ======================

if __name__ == "__main__":
    # 从环境变量获取端口
    port = int(os.environ.get('PORT', 5001))
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=port, debug=True)
