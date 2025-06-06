#!/usr/bin/env python3
"""
GPU集群资源管理系统
支持多种GPU类型（NVIDIA, Apple Silicon等）并允许动态添加新节点/集群
"""

import abc
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gpu_cluster")

# ====================== 数据模型 ======================

class GPUType(Enum):
    """GPU类型枚举"""
    NVIDIA = "nvidia"
    APPLE = "apple"
    AMD = "amd"
    INTEL = "intel"
    UNKNOWN = "unknown"

@dataclass
class GPUInfo:
    """GPU信息"""
    id: str
    name: str
    memory_total: int  # MB
    gpu_type: GPUType
    compute_capability: Optional[str] = None
    extra_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NodeInfo:
    """节点信息"""
    id: str
    name: str
    ip: str
    port: int
    gpus: List[GPUInfo] = field(default_factory=list)
    status: str = "unknown"  # unknown, online, offline, busy
    last_heartbeat: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 新增字段
    memory_total: int = 0  # 总内存，单位MB
    memory_available: int = 0  # 可用内存，单位MB
    cpu_info: Dict[str, Any] = field(default_factory=dict)  # CPU信息，包含核心数、型号等

@dataclass
class ClusterInfo:
    """集群信息"""
    id: str
    name: str
    nodes: List[NodeInfo] = field(default_factory=list)
    adapter_type: str = ""
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Task:
    """计算任务"""
    id: str
    name: str
    requirements: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed
    assigned_node: Optional[str] = None
    assigned_gpu: Optional[str] = None
    result: Any = None

# ====================== 抽象接口 ======================

class GPUAdapter(abc.ABC):
    """GPU适配器抽象基类"""
    
    @abc.abstractmethod
    def get_adapter_type(self) -> str:
        """获取适配器类型"""
        pass
    
    @abc.abstractmethod
    def discover_nodes(self, config: Dict[str, Any]) -> List[NodeInfo]:
        """发现节点"""
        pass
    
    @abc.abstractmethod
    def get_gpu_info(self, node: NodeInfo) -> List[GPUInfo]:
        """获取GPU信息"""
        pass
    
    @abc.abstractmethod
    def check_node_status(self, node: NodeInfo) -> str:
        """检查节点状态"""
        pass
    
    @abc.abstractmethod
    def execute_task(self, node: NodeInfo, gpu: GPUInfo, task: Task) -> Any:
        """执行任务"""
        pass
        
    @abc.abstractmethod
    def build_container_command(self, node: NodeInfo, gpus: List[str], params: Dict[str, Any]) -> str:
        """
        构建容器运行命令
        
        Args:
            node: 节点信息
            gpus: GPU ID列表
            params: 运行参数，包含以下字段：
                - host: 主机地址
                - port: 端口列表
                - model_path: 模型路径
                - log_path: 日志路径
                - docker_image: Docker镜像
                - docker_name: 容器名称
                - python: Python解释器路径
                - controller_address: 控制器地址
                - model_names: 模型名称
                - other_params: 其他参数
                
        Returns:
            str: 构建的容器运行命令
        """
        pass

# ====================== 适配器实现 ======================

class MuxiGPUAdapter(GPUAdapter):
    """沐曦GPU适配器"""
    
    def get_adapter_type(self) -> str:
        return "muxi"
    
    def discover_nodes(self, config: Dict[str, Any]) -> List[NodeInfo]:
        """发现沐曦GPU节点"""
        logger.info(f"Discovering Muxi nodes with config: {config}")
        nodes = []
        
        # 从配置中读取节点信息
        for node_config in config.get("nodes", []):
            node_id = node_config.get("id", str(uuid.uuid4()))
            node_name = node_config.get("name", f"muxi-node-{node_id}")
            node_ip = node_config.get("ip", "")
            node_port = node_config.get("port", 22)
            
            if not node_ip:
                logger.warning(f"Skipping node {node_name} with empty IP")
                continue
            
            # 创建节点信息
            node = NodeInfo(
                id=node_id,
                name=node_name,
                ip=node_ip,
                port=node_port,
                status="unknown"
            )
            
            # 获取GPU信息
            try:
                node.gpus = self.get_gpu_info(node)
                node.status = self.check_node_status(node)
                node.last_heartbeat = time.time()
                
                # 获取节点系统信息
                node.memory_total = node_config.get("memory_total", 0)
                node.memory_available = node_config.get("memory_available", 0)
                node.cpu_info = node_config.get("cpu_info", {})
                
                nodes.append(node)
                logger.info(f"Discovered Muxi node: {node.name} ({node.ip}) with {len(node.gpus)} GPUs")
            except Exception as e:
                logger.error(f"Error discovering Muxi node {node_name} ({node_ip}): {str(e)}")
        
        return nodes
    
    def get_gpu_info(self, node: NodeInfo) -> List[GPUInfo]:
        """获取沐曦GPU信息"""
        logger.info(f"Getting GPU info for Muxi node: {node.name} ({node.ip})")
        gpus = []
        
        try:
            # 使用mx-smi命令获取沐曦GPU信息
            # 在实际实现中，通过SSH执行mx-smi命令获取GPU信息
            # 以下是示例代码，实际实现需要根据沐曦GPU的特性进行调整
            
            # 模拟SSH执行mx-smi命令
            # 实际代码应该类似于：
            # ssh_client = paramiko.SSHClient()
            # ssh_client.connect(node.ip, port=node.port, username=username, password=password)
            # stdin, stdout, stderr = ssh_client.exec_command('mx-smi --query-gpu=index,name,memory.total --format=csv,noheader,nounits')
            # mx_smi_output = stdout.read().decode('utf-8').strip().split('\n')
            
            # 模拟mx-smi输出
            mx_smi_output = [
                "0, MXC500, 65536",
                "1, MXC500, 65536"
            ]
            
            for line in mx_smi_output:
                parts = line.split(",")
                if len(parts) >= 3:
                    gpu_id = parts[0].strip()
                    gpu_name = parts[1].strip()
                    memory_total = int(parts[2].strip())
                    
                    gpu = GPUInfo(
                        id=gpu_id,
                        name=gpu_name,
                        memory_total=memory_total,
                        gpu_type=GPUType.UNKNOWN,  # 可以定义一个新的枚举值 GPUType.MUXI
                        compute_capability="1.0"  # 沐曦GPU的计算能力版本
                    )
                    
                    # 可以添加额外信息
                    gpu.extra_info = {
                        "driver_version": "1.0.0",  # 假设的驱动版本
                        "utilization": 0  # 初始利用率为0
                    }
                    
                    gpus.append(gpu)
            
            logger.info(f"Found {len(gpus)} Muxi GPUs on node {node.name} using mx-smi")
        except Exception as e:
            logger.error(f"Error getting Muxi GPU info for node {node.name}: {str(e)}")
        
        return gpus
    
    def check_node_status(self, node: NodeInfo) -> str:
        """检查沐曦节点状态"""
        logger.info(f"Checking status for Muxi node: {node.name} ({node.ip})")
        
        try:
            # 这里应该实现检查沐曦节点状态的逻辑
            # 例如通过SSH执行命令检查节点状态
            # 以下是示例代码，实际实现需要根据沐曦GPU的特性进行调整
            
            # 模拟检查节点状态
            # 在实际实现中，可以通过SSH执行ping或其他命令检查节点状态
            status = "online"  # 假设节点在线
            
            logger.info(f"Muxi node {node.name} status: {status}")
            return status
        except Exception as e:
            logger.error(f"Error checking Muxi node {node.name} status: {str(e)}")
            return "offline"
    
    def execute_task(self, node: NodeInfo, gpu: GPUInfo, task: Task) -> Any:
        """在沐曦GPU上执行任务"""
        logger.info(f"Executing task {task.name} on Muxi node {node.name}, GPU {gpu.id}")
        
        try:
            # 这里应该实现在沐曦GPU上执行任务的逻辑
            # 例如通过SSH执行命令或通过API调用执行任务
            # 以下是示例代码，实际实现需要根据沐曦GPU的特性进行调整
            
            # 模拟执行任务
            # 在实际实现中，可以通过SSH执行命令或通过API调用执行任务
            result = f"Task {task.name} executed on Muxi GPU {gpu.id}"
            
            logger.info(f"Task {task.name} executed successfully on Muxi node {node.name}, GPU {gpu.id}")
            return result
        except Exception as e:
            logger.error(f"Error executing task {task.name} on Muxi node {node.name}, GPU {gpu.id}: {str(e)}")
            raise
        
    def build_container_command(self, node: NodeInfo, gpus: List[str], params: Dict[str, Any]) -> str:
        """构建沐曦GPU容器运行命令"""
        logger.info(f"Building container command for Muxi node {node.name} with GPUs {gpus}")
        
        # 获取参数
        host = params.get("host", "0.0.0.0")
        ports = params.get("port", [])
        model_path = params.get("model_path", "/models")
        log_path = params.get("log_path", "/logs")
        docker_image = params.get("docker_image", "")
        docker_name = params.get("docker_name", "")
        python = params.get("python", "python")
        controller_address = params.get("controller_address", "")
        model_names = params.get("model_names", "")
        other_params = params.get("other_params", "")
        
        # 检查必要参数
        if not docker_image or not docker_name or not ports:
            logger.error("Missing required parameters for container command")
            return ""
        
        # 构建GPU设备参数
        gpus_str = ",".join(gpus)
        
        # 构建路径映射
        model_path_volume = f"{model_path}:/models"
        log_path_volume = f"{log_path}:/logs"
        
        # 构建沐曦GPU特有的参数
        # 沐曦GPU需要特殊的设备参数和环境变量
        muxi_specific_params = "--device=/dev/dri --device=/dev/mxcd --group-add video -e MCCL_SOCKET_IFNAME=ens1np0"
        
        # 构建完整的命令
        port_idx = 0  # 使用第一个端口
        port = ports[port_idx] if port_idx < len(ports) else 8000
        
        command = f"docker run --network=host -p {port}:{port} -v {log_path_volume} \
-v {model_path_volume} -e MX_VISIBLE_DEVICES={gpus_str} \
{muxi_specific_params} --name {docker_name} {docker_image} {python} \
/fschat/general_worker.py --host {host} --port {port} \
--model-path {model_path} --controller-address {controller_address} \
--worker-address http://{host}:{port} --model-names {model_names} \
--log-dir {log_path} --gpus 0 {other_params} --docker-name {docker_name}"
        
        logger.info(f"Built container command: {command}")
        return command


class NvidiaGPUAdapter(GPUAdapter):
    """NVIDIA GPU适配器"""
    
    def get_adapter_type(self) -> str:
        return "nvidia"
    
    def discover_nodes(self, config: Dict[str, Any]) -> List[NodeInfo]:
        """发现NVIDIA GPU节点"""
        logger.info(f"Discovering NVIDIA nodes with config: {config}")
        nodes = []
        
        # 从配置中读取节点信息
        for node_config in config.get("nodes", []):
            node = NodeInfo(
                id=node_config.get("id", str(uuid.uuid4())),
                name=node_config.get("name", f"nvidia-node-{len(nodes)}"),
                ip=node_config.get("ip", "127.0.0.1"),
                port=node_config.get("port", 22),
                status="unknown"
            )
            
            # 获取节点的内存和CPU信息
            try:
                import paramiko
                import re
                
                # 创建SSH客户端
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # 尝试从节点元数据中获取凭据
                username = node_config.get("metadata", {}).get("username", "root")
                password = node_config.get("metadata", {}).get("password", "")
                
                try:
                    # 连接到远程服务器
                    ssh.connect(node.ip, node.port, username, password)
                    
                    # 获取内存信息
                    stdin, stdout, stderr = ssh.exec_command("free -m | grep Mem")
                    mem_output = stdout.read().decode("utf-8")
                    mem_parts = mem_output.split()
                    if len(mem_parts) >= 7:
                        node.memory_total = int(mem_parts[1])
                        node.memory_available = int(mem_parts[6])
                    
                    # 获取CPU信息
                    stdin, stdout, stderr = ssh.exec_command("lscpu")
                    cpu_output = stdout.read().decode("utf-8")
                    
                    # 解析CPU信息
                    cpu_info = {}
                    for line in cpu_output.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            cpu_info[key.strip()] = value.strip()
                    
                    # 提取关键信息
                    node.cpu_info = {
                        "model": cpu_info.get("Model name", "Unknown"),
                        "cores": int(cpu_info.get("CPU(s)", 0)),
                        "architecture": cpu_info.get("Architecture", "Unknown"),
                        "vendor": cpu_info.get("Vendor ID", "Unknown")
                    }
                    
                    # 获取主机名和操作系统信息
                    stdin, stdout, stderr = ssh.exec_command("hostname")
                    hostname = stdout.read().decode("utf-8").strip()
                    
                    stdin, stdout, stderr = ssh.exec_command("uname -a")
                    os_info = stdout.read().decode("utf-8").strip()
                    
                    # 更新节点元数据
                    node.metadata.update({
                        "hostname": hostname,
                        "os": os_info.split()[0],
                        "os_version": " ".join(os_info.split()[2:])
                    })
                    
                finally:
                    ssh.close()
                    
            except Exception as e:
                logger.error(f"Error getting node system info: {e}")
            
            nodes.append(node)
            
        return nodes
    
    def get_gpu_info(self, node: NodeInfo) -> List[GPUInfo]:
        """获取NVIDIA GPU信息"""
        logger.info(f"Getting GPU info for NVIDIA node: {node.name}")
        
        # 使用SSH连接到远程服务器并获取GPU信息
        gpus = []
        
        try:
            import paramiko
            import re
            
            # 创建SSH客户端
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 如果节点是本地节点，直接使用本地命令
            if node.ip in ["127.0.0.1", "localhost"] and os.path.exists("/usr/bin/nvidia-smi"):
                import subprocess
                output = subprocess.check_output(["nvidia-smi", "--query-gpu=index,name,memory.total,driver_version", "--format=csv,noheader"]).decode("utf-8")
                lines = output.strip().split("\n")
            else:
                # 连接到远程服务器
                # 注意：在实际生产环境中，应该使用密钥认证而不是密码
                try:
                    # 尝试从节点元数据中获取凭据
                    username = node.metadata.get("username", "root")
                    password = node.metadata.get("password", "")
                    ssh.connect(node.ip, node.port, username, password)
                    
                    # 执行nvidia-smi命令获取GPU信息
                    stdin, stdout, stderr = ssh.exec_command("nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader")
                    output = stdout.read().decode("utf-8")
                    lines = output.strip().split("\n")
                finally:
                    ssh.close()
            
            # 解析输出并创建GPU对象
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
                    
                    # 生成模拟的GPU占用率，基于GPU ID生成一致的随机值
                    # 这样同一个GPU每次都会显示相同的占用率
                    import hashlib
                    gpu_id_hash = hashlib.md5(f"{node.id}-gpu-{index}".encode()).hexdigest()
                    usage_seed = int(gpu_id_hash[:8], 16) % 100  # 生成固定的占用率值(0-99)
                    
                    # 创建GPU对象
                    gpu = GPUInfo(
                        id=f"{node.id}-gpu-{index}",
                        name=name,
                        memory_total=memory_total,
                        gpu_type=GPUType.NVIDIA,
                        compute_capability="Unknown",  # 无法从nvidia-smi直接获取计算能力
                        extra_info={
                            "driver_version": driver_version,
                            "cuda_version": cuda_version,
                            "usage": usage_seed  # 添加GPU占用率信息
                        }
                    )
                    gpus.append(gpu)
                
        except Exception as e:
            logger.error(f"Error getting NVIDIA GPU info: {e}")
            # 如果无法获取实际GPU信息，返回一个模拟的GPU
            # 这样至少系统可以继续工作
            import hashlib
            import random
            
            # 生成模拟的GPU占用率
            gpu_id = f"{node.id}-gpu-0"
            gpu_id_hash = hashlib.md5(gpu_id.encode()).hexdigest()
            usage_seed = int(gpu_id_hash[:8], 16) % 100  # 生成固定的占用率值(0-99)
            
            gpu = GPUInfo(
                id=gpu_id,
                name="NVIDIA GPU (Simulated)",
                memory_total=16384,  # 16GB
                gpu_type=GPUType.NVIDIA,  # 保持为NVIDIA类型，因为这是NVIDIA适配器
                extra_info={
                    "note": "This is a simulated GPU because actual GPU info could not be retrieved",
                    "error": str(e),
                    "usage": usage_seed  # 添加GPU占用率信息
                }
            )
            gpus.append(gpu)
            
        return gpus
    
    def check_node_status(self, node: NodeInfo) -> str:
        """检查NVIDIA节点状态"""
        # 实际实现会ping节点或检查服务状态
        # 这里简单模拟
        current_time = time.time()
        if current_time - node.last_heartbeat > 60:  # 1分钟没有心跳
            return "offline"
        return "online"
    
    def execute_task(self, node: NodeInfo, gpu: GPUInfo, task: Task) -> Any:
        """在NVIDIA GPU上执行任务"""
        logger.info(f"Executing task {task.id} on NVIDIA node {node.name}, GPU {gpu.id}")
        
        # 实际实现会通过SSH或API在远程节点上执行任务
        # 这里简单模拟执行过程
        task.status = "running"
        
        # 模拟任务执行
        time.sleep(1)  # 实际任务会花费更长时间
        
        # 返回结果
        result = {
            "status": "success",
            "execution_time": 1.0,
            "output": f"Task {task.id} completed on NVIDIA GPU {gpu.id}"
        }
        
        task.status = "completed"
        task.result = result
        
        return result
        
    def build_container_command(self, node: NodeInfo, gpus: List[str], params: Dict[str, Any]) -> str:
        """构建NVIDIA GPU容器运行命令"""
        logger.info(f"Building container command for NVIDIA node {node.name} with GPUs {gpus}")
        
        # 获取参数
        host = params.get("host", "0.0.0.0")
        ports = params.get("port", [])
        model_path = params.get("model_path", "/models")
        log_path = params.get("log_path", "/logs")
        docker_image = params.get("docker_image", "")
        docker_name = params.get("docker_name", "")
        python = params.get("python", "python")
        controller_address = params.get("controller_address", "")
        model_names = params.get("model_names", "")
        other_params = params.get("other_params", "")
        
        # 检查必要参数
        if not docker_image or not docker_name or not ports:
            logger.error("Missing required parameters for container command")
            return ""
        
        # 构建GPU设备参数
        gpus_str = ",".join(gpus)
        
        # 构建路径映射
        model_path_volume = f"{model_path}:/models"
        log_path_volume = f"{log_path}:/logs"
        
        # 构建完整的命令
        port_idx = 0  # 使用第一个端口
        port = ports[port_idx] if port_idx < len(ports) else 8000
        
        command = f"docker run --network=host -p {port}:{port} -v {log_path_volume} \
-v {model_path_volume} -e NVIDIA_VISIBLE_DEVICES={gpus_str} \
--gpus all --name {docker_name} {docker_image} {python} \
/fschat/general_worker.py --host {host} --port {port} \
--model-path {model_path} --controller-address {controller_address} \
--worker-address http://{host}:{port} --model-names {model_names} \
--log-dir {log_path} --gpus 0 {other_params} --docker-name {docker_name}"
        
        logger.info(f"Built container command: {command}")
        return command

class AppleGPUAdapter(GPUAdapter):
    """Apple Silicon GPU适配器"""
    
    def get_adapter_type(self) -> str:
        return "apple"
    
    def discover_nodes(self, config: Dict[str, Any]) -> List[NodeInfo]:
        """发现Apple Silicon节点"""
        logger.info(f"Discovering Apple Silicon nodes with config: {config}")
        nodes = []
        
        # 从配置中读取节点信息
        for node_config in config.get("nodes", []):
            # 获取实际的主机名和系统信息
            import platform
            import socket
            import subprocess
            import re
            
            try:
                hostname = platform.node()
                ip_address = socket.gethostbyname(socket.gethostname())
                
                # 获取更多系统信息
                os_info = platform.system() + " " + platform.release()
                
                # 获取CPU信息
                cpu_model = ""
                cpu_cores = 0
                cpu_arch = ""
                
                # 获取内存信息
                memory_total = 0
                memory_available = 0
                
                if platform.system() == "Darwin":  # macOS
                    try:
                        # 获取CPU型号
                        cmd = "sysctl -n machdep.cpu.brand_string"
                        cpu_model = subprocess.check_output(cmd, shell=True).decode().strip()
                        if not cpu_model or "Apple" not in cpu_model:
                            cpu_model = "Apple Silicon"
                            
                        # 获取CPU核心数
                        cmd = "sysctl -n hw.ncpu"
                        cpu_cores = int(subprocess.check_output(cmd, shell=True).decode().strip())
                        
                        # 获取CPU架构
                        cmd = "uname -m"
                        cpu_arch = subprocess.check_output(cmd, shell=True).decode().strip()
                        
                        # 获取总内存
                        cmd = "sysctl -n hw.memsize"
                        mem_bytes = int(subprocess.check_output(cmd, shell=True).decode().strip())
                        memory_total = mem_bytes // (1024 * 1024)  # 转换为MB
                        
                        # 获取可用内存
                        cmd = "vm_stat"
                        vm_stat = subprocess.check_output(cmd, shell=True).decode()
                        page_size_match = re.search(r'page size of (\d+) bytes', vm_stat)
                        pages_free_match = re.search(r'Pages free:\s+(\d+)', vm_stat)
                        
                        if page_size_match and pages_free_match:
                            page_size = int(page_size_match.group(1))
                            pages_free = int(pages_free_match.group(1))
                            memory_available = (pages_free * page_size) // (1024 * 1024)  # 转换为MB
                    except Exception as e:
                        logger.error(f"Error getting system info: {e}")
                        cpu_model = "Apple Silicon"
                        cpu_cores = 10  # 默认值
                        cpu_arch = "arm64"  # 默认值
                        memory_total = 16384  # 默认值 16GB
                        memory_available = 8192  # 默认值 8GB
            except Exception as e:
                logger.error(f"Error getting basic system info: {e}")
                hostname = node_config.get("name", "localhost")
                ip_address = node_config.get("ip", "127.0.0.1")
                os_info = "macOS"
                cpu_model = "Apple Silicon"
                cpu_cores = 10  # 默认值
                cpu_arch = "arm64"  # 默认值
                memory_total = 16384  # 默认值 16GB
                memory_available = 8192  # 默认值 8GB
            
            # 创建单个真实节点
            node = NodeInfo(
                id=node_config.get("id", str(uuid.uuid4())),
                name=hostname,
                ip=ip_address,
                port=node_config.get("port", 22),
                status="online",  # 默认为在线状态
                memory_total=memory_total,
                memory_available=memory_available,
                cpu_info={
                    "model": cpu_model,
                    "cores": cpu_cores,
                    "architecture": cpu_arch
                },
                metadata={
                    "node_type": "master",
                    "os": os_info,
                    "hostname": hostname,
                    "description": node_config.get("description", "M3 Max单节点集群")
                }
            )
            nodes.append(node)
            
        return nodes
    
    def get_gpu_info(self, node: NodeInfo) -> List[GPUInfo]:
        """获取Apple Silicon GPU信息"""
        logger.info(f"Getting GPU info for Apple Silicon node: {node.name}")
        
        gpus = []
        
        try:
            import platform
            import subprocess
            import re
            
            # 获取实际的Mac型号
            mac_model = "M3 Max"  # 默认值
            memory_total = 32768  # 默认值，32GB
            gpu_cores = 40        # 默认值，40核心
            
            try:
                # 尝试从系统信息中获取Mac型号
                cmd = "system_profiler SPHardwareDataType"
                hardware_info = subprocess.check_output(cmd, shell=True).decode().strip()
                
                # 提取型号
                model_match = re.search(r'Model Name:\s*(.+)', hardware_info)
                if model_match:
                    mac_model = model_match.group(1).strip()
                
                # 提取内存
                memory_match = re.search(r'Memory:\s*(\d+)\s*GB', hardware_info)
                if memory_match:
                    memory_gb = int(memory_match.group(1))
                    memory_total = memory_gb * 1024  # 转换为MB
                
                # 尝试获取GPU核心数
                if "M3 Max" in mac_model:
                    # M3 Max有两种配置：30核心和40核心
                    gpu_cores = 40  # 默认使用高配置
                elif "M3 Pro" in mac_model:
                    gpu_cores = 19
                elif "M3" in mac_model:
                    gpu_cores = 10
                elif "M2 Max" in mac_model:
                    gpu_cores = 38
                elif "M2 Pro" in mac_model:
                    gpu_cores = 19
                elif "M2" in mac_model:
                    gpu_cores = 10
                elif "M1 Max" in mac_model:
                    gpu_cores = 32
                elif "M1 Pro" in mac_model:
                    gpu_cores = 16
                elif "M1" in mac_model:
                    gpu_cores = 8
            except Exception as e:
                logger.warning(f"Error getting detailed hardware info: {e}")
            
            # 创建真实GPU信息
            gpu = GPUInfo(
                id=f"{node.id}-gpu-0",
                name=f"Apple {mac_model} GPU",
                memory_total=memory_total,  # 实际内存大小
                gpu_type=GPUType.APPLE,
                extra_info={
                    "cores": gpu_cores,
                    "metal_version": "3.0",
                    "chip_model": mac_model,
                    "unified_memory": True
                }
            )
            gpus.append(gpu)
                
        except Exception as e:
            logger.error(f"Error getting Apple GPU info: {e}")
            
        return gpus
    
    def check_node_status(self, node: NodeInfo) -> str:
        """检查Apple节点状态"""
        # 实际实现会ping节点或检查服务状态
        current_time = time.time()
        if current_time - node.last_heartbeat > 60:  # 1分钟没有心跳
            return "offline"
        return "online"
    
    def execute_task(self, node: NodeInfo, gpu: GPUInfo, task: Task) -> Any:
        """在Apple GPU上执行任务"""
        logger.info(f"Executing task {task.id} on Apple node {node.name}, GPU {gpu.id}")
        
        # 实际实现会通过SSH或API在远程节点上执行任务
        task.status = "running"
        
        # 模拟任务执行
        time.sleep(1)
        
        # 返回结果
        result = {
            "status": "success",
            "execution_time": 1.0,
            "output": f"Task {task.id} completed on Apple GPU {gpu.id}"
        }
        
        task.status = "completed"
        task.result = result
        
        return result
        
    def build_container_command(self, node: NodeInfo, gpus: List[str], params: Dict[str, Any]) -> str:
        """构建Apple GPU容器运行命令"""
        logger.info(f"Building container command for Apple node {node.name} with GPUs {gpus}")
        
        # 获取参数
        host = params.get("host", "0.0.0.0")
        ports = params.get("port", [])
        model_path = params.get("model_path", "/models")
        log_path = params.get("log_path", "/logs")
        docker_image = params.get("docker_image", "")
        docker_name = params.get("docker_name", "")
        python = params.get("python", "python")
        controller_address = params.get("controller_address", "")
        model_names = params.get("model_names", "")
        other_params = params.get("other_params", "")
        
        # 检查必要参数
        if not docker_image or not docker_name or not ports:
            logger.error("Missing required parameters for container command")
            return ""
        
        # 构建路径映射
        model_path_volume = f"{model_path}:/models"
        log_path_volume = f"{log_path}:/logs"
        
        # 构建完整的命令
        port_idx = 0  # 使用第一个端口
        port = ports[port_idx] if port_idx < len(ports) else 8000
        
        # Apple Silicon特有的参数
        apple_specific_params = "--platform linux/arm64"
        
        command = f"docker run --network=host -p {port}:{port} -v {log_path_volume} \
-v {model_path_volume} {apple_specific_params} \
--name {docker_name} {docker_image} {python} \
/fschat/general_worker.py --host {host} --port {port} \
--model-path {model_path} --controller-address {controller_address} \
--worker-address http://{host}:{port} --model-names {model_names} \
--log-dir {log_path} {other_params} --docker-name {docker_name}"
        
        logger.info(f"Built container command: {command}")
        return command

# ====================== 资源管理 ======================

class ResourceRegistry:
    """资源注册中心"""
    
    def __init__(self):
        self.clusters: Dict[str, ClusterInfo] = {}
        self.adapters: Dict[str, GPUAdapter] = {}
        
    def register_adapter(self, adapter: GPUAdapter):
        """注册GPU适配器"""
        adapter_type = adapter.get_adapter_type()
        logger.info(f"Registering adapter for {adapter_type}")
        self.adapters[adapter_type] = adapter
        
    def add_cluster(self, cluster: ClusterInfo) -> bool:
        """添加集群"""
        if cluster.id in self.clusters:
            logger.warning(f"Cluster {cluster.id} already exists")
            return False
            
        self.clusters[cluster.id] = cluster
        logger.info(f"Added cluster: {cluster.name} ({cluster.id})")
        return True
        
    def remove_cluster(self, cluster_id: str) -> bool:
        """移除集群"""
        if cluster_id not in self.clusters:
            logger.warning(f"Cluster {cluster_id} not found")
            return False
            
        del self.clusters[cluster_id]
        logger.info(f"Removed cluster: {cluster_id}")
        return True
        
    def get_cluster(self, cluster_id: str) -> Optional[ClusterInfo]:
        """获取集群信息"""
        return self.clusters.get(cluster_id)
        
    def list_clusters(self) -> List[ClusterInfo]:
        """列出所有集群"""
        return list(self.clusters.values())
        
    def discover_cluster(self, name: str, adapter_type: str, config: Dict[str, Any]) -> Optional[ClusterInfo]:
        """发现并添加新集群"""
        if adapter_type not in self.adapters:
            logger.error(f"No adapter found for type: {adapter_type}")
            return None
            
        adapter = self.adapters[adapter_type]
        
        # 创建新集群
        cluster_id = str(uuid.uuid4())
        cluster = ClusterInfo(
            id=cluster_id,
            name=name,
            adapter_type=adapter_type,
            config=config
        )
        
        # 发现节点
        nodes = adapter.discover_nodes(config)
        for node in nodes:
            # 获取每个节点的GPU信息
            gpus = adapter.get_gpu_info(node)
            node.gpus = gpus
            node.status = adapter.check_node_status(node)
            node.last_heartbeat = time.time()
            
            # 添加到集群
            cluster.nodes.append(node)
            
        # 添加集群到注册中心
        self.add_cluster(cluster)
        
        return cluster
        
    def update_cluster_status(self, cluster_id: str) -> bool:
        """更新集群状态"""
        cluster = self.get_cluster(cluster_id)
        if not cluster:
            return False
            
        adapter = self.adapters.get(cluster.adapter_type)
        if not adapter:
            return False
            
        for node in cluster.nodes:
            # 更新节点状态
            node.status = adapter.check_node_status(node)
            
            # 如果节点在线，更新GPU信息
            if node.status == "online":
                node.gpus = adapter.get_gpu_info(node)
                node.last_heartbeat = time.time()
                
        return True
        
    def find_available_gpu(self, requirements: Dict[str, Any]) -> Tuple[Optional[NodeInfo], Optional[GPUInfo]]:
        """根据需求查找可用GPU"""
        required_type = requirements.get("gpu_type")
        required_memory = requirements.get("min_memory", 0)
        
        for cluster in self.clusters.values():
            for node in cluster.nodes:
                if node.status != "online":
                    continue
                    
                for gpu in node.gpus:
                    # 检查GPU类型
                    if required_type and gpu.gpu_type.value != required_type:
                        continue
                        
                    # 检查内存要求
                    if gpu.memory_total < required_memory:
                        continue
                        
                    # 找到符合要求的GPU
                    return node, gpu
                    
        return None, None

# ====================== 任务调度 ======================

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, registry: ResourceRegistry):
        self.registry = registry
        self.tasks: Dict[str, Task] = {}
        self.pending_tasks: List[str] = []
        self.running_tasks: Dict[str, Tuple[str, str]] = {}  # task_id -> (node_id, gpu_id)
        
    def submit_task(self, task: Task) -> str:
        """提交任务"""
        self.tasks[task.id] = task
        self.pending_tasks.append(task.id)
        logger.info(f"Task submitted: {task.id}")
        return task.id
        
    def process_pending_tasks(self):
        """处理待处理任务"""
        if not self.pending_tasks:
            return
            
        # 处理每个待处理任务
        remaining_tasks = []
        for task_id in self.pending_tasks:
            task = self.tasks.get(task_id)
            if not task:
                continue
                
            # 查找可用资源
            node, gpu = self.registry.find_available_gpu(task.requirements)
            if not node or not gpu:
                # 没有找到合适的资源，保留在待处理列表
                remaining_tasks.append(task_id)
                continue
                
            # 分配资源并执行任务
            self._execute_task(task, node, gpu)
            
        self.pending_tasks = remaining_tasks
        
    def _execute_task(self, task: Task, node: NodeInfo, gpu: GPUInfo):
        """执行任务"""
        # 更新任务状态
        task.assigned_node = node.id
        task.assigned_gpu = gpu.id
        
        # 记录运行中的任务
        self.running_tasks[task.id] = (node.id, gpu.id)
        
        # 获取适配器
        cluster = next((c for c in self.registry.clusters.values() 
                      if any(n.id == node.id for n in c.nodes)), None)
        if not cluster:
            logger.error(f"Cannot find cluster for node {node.id}")
            task.status = "failed"
            return
            
        adapter = self.registry.adapters.get(cluster.adapter_type)
        if not adapter:
            logger.error(f"Cannot find adapter for type {cluster.adapter_type}")
            task.status = "failed"
            return
            
        # 异步执行任务（在实际实现中，这应该是异步的）
        try:
            result = adapter.execute_task(node, gpu, task)
            task.result = result
            task.status = "completed"
        except Exception as e:
            logger.error(f"Error executing task {task.id}: {e}")
            task.status = "failed"
        finally:
            # 清理运行中的任务记录
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]

# ====================== 配置管理 ======================

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if not os.path.exists(self.config_path):
            return {"clusters": {}}
            
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"clusters": {}}
            
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            
    def get_cluster_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有集群配置"""
        return self.config.get("clusters", {})
        
    def add_cluster_config(self, name: str, adapter_type: str, config: Dict[str, Any]) -> str:
        """添加集群配置"""
        cluster_id = str(uuid.uuid4())
        
        if "clusters" not in self.config:
            self.config["clusters"] = {}
            
        self.config["clusters"][cluster_id] = {
            "name": name,
            "adapter_type": adapter_type,
            "config": config
        }
        
        self.save_config()
        return cluster_id
        
    def remove_cluster_config(self, cluster_id: str) -> bool:
        """移除集群配置"""
        if "clusters" not in self.config or cluster_id not in self.config["clusters"]:
            return False
            
        del self.config["clusters"][cluster_id]
        self.save_config()
        return True
        
    def update_cluster_config(self, cluster_id: str, config: Dict[str, Any]) -> bool:
        """更新集群配置"""
        if "clusters" not in self.config or cluster_id not in self.config["clusters"]:
            return False
            
        self.config["clusters"][cluster_id]["config"] = config
        self.save_config()
        return True

# ====================== 主控制器 ======================

class ClusterController:
    """集群控制器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_manager = ConfigManager(config_path)
        self.registry = ResourceRegistry()
        self.scheduler = TaskScheduler(self.registry)
        
        # 注册适配器
        self.registry.register_adapter(NvidiaGPUAdapter())
        self.registry.register_adapter(AppleGPUAdapter())
        self.registry.register_adapter(MuxiGPUAdapter())
        
    def initialize(self):
        """初始化系统"""
        # 加载配置的集群
        cluster_configs = self.config_manager.get_cluster_configs()
        for cluster_id, cluster_config in cluster_configs.items():
            name = cluster_config["name"]
            adapter_type = cluster_config["adapter_type"]
            config = cluster_config["config"]
            
            # 发现并添加集群
            self.registry.discover_cluster(name, adapter_type, config)
            
        logger.info(f"Initialized with {len(self.registry.clusters)} clusters")
        
    def add_cluster(self, name: str, adapter_type: str, config: Dict[str, Any]) -> str:
        """添加新集群"""
        # 添加到配置
        cluster_id = self.config_manager.add_cluster_config(name, adapter_type, config)
        
        # 发现并添加集群
        cluster = self.registry.discover_cluster(name, adapter_type, config)
        
        return cluster_id if cluster else ""
        
    def remove_cluster(self, cluster_id: str) -> bool:
        """移除集群"""
        # 从配置中移除
        self.config_manager.remove_cluster_config(cluster_id)
        
        # 从注册中心移除
        return self.registry.remove_cluster(cluster_id)
        
    def update_cluster(self, cluster_id: str, config: Dict[str, Any]) -> bool:
        """更新集群配置"""
        # 更新配置
        self.config_manager.update_cluster_config(cluster_id, config)
        
        # 重新发现集群
        cluster = self.registry.get_cluster(cluster_id)
        if not cluster:
            return False
            
        self.registry.remove_cluster(cluster_id)
        self.registry.discover_cluster(cluster.name, cluster.adapter_type, config)
        
        return True
        
    def list_clusters(self) -> List[Dict[str, Any]]:
        """列出所有集群"""
        clusters = []
        for cluster in self.registry.list_clusters():
            cluster_info = {
                "id": cluster.id,
                "name": cluster.name,
                "adapter_type": cluster.adapter_type,
                "node_count": len(cluster.nodes),
                "gpu_count": sum(len(node.gpus) for node in cluster.nodes),
                "nodes": []
            }
            
            # 添加节点信息
            for node in cluster.nodes:
                node_info = {
                    "id": node.id,
                    "name": node.name,
                    "ip": node.ip,
                    "status": node.status,
                    "gpus": [{"id": gpu.id, "name": gpu.name, "memory": gpu.memory_total} 
                             for gpu in node.gpus]
                }
                cluster_info["nodes"].append(node_info)
                
            clusters.append(cluster_info)
            
        return clusters
        
    def submit_task(self, name: str, requirements: Dict[str, Any]) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            requirements=requirements
        )
        
        return self.scheduler.submit_task(task)
        
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        task = self.scheduler.tasks.get(task_id)
        if not task:
            return {"status": "not_found"}
            
        result = {
            "id": task.id,
            "name": task.name,
            "status": task.status
        }
        
        if task.assigned_node:
            result["assigned_node"] = task.assigned_node
            
        if task.assigned_gpu:
            result["assigned_gpu"] = task.assigned_gpu
            
        if task.result:
            result["result"] = task.result
            
        return result
        
    def run_scheduler(self):
        """运行调度器"""
        # 更新所有集群状态
        for cluster_id in self.registry.clusters:
            self.registry.update_cluster_status(cluster_id)
            
        # 处理待处理任务
        self.scheduler.process_pending_tasks()

# ====================== 示例使用 ======================

def main():
    """主函数"""
    # 创建控制器
    controller = ClusterController("gpu_clusters.json")
    
    # 初始化
    controller.initialize()
    
    # 添加NVIDIA集群
    nvidia_config = {
        "nodes": [
            {"name": "nvidia-node-1", "ip": "192.168.1.101", "port": 22, "gpu_count": 4},
            {"name": "nvidia-node-2", "ip": "192.168.1.102", "port": 22, "gpu_count": 8}
        ]
    }
    nvidia_cluster_id = controller.add_cluster("NVIDIA Cluster", "nvidia", nvidia_config)
    
    # 添加Apple集群
    apple_config = {
        "nodes": [
            {"name": "mac-node-1", "ip": "192.168.1.201", "port": 22, "gpu_model": "M2 Max"},
            {"name": "mac-node-2", "ip": "192.168.1.202", "port": 22, "gpu_model": "M3 Ultra"}
        ]
    }
    apple_cluster_id = controller.add_cluster("Apple Silicon Cluster", "apple", apple_config)
    
    # 列出集群
    clusters = controller.list_clusters()
    print(f"Available clusters: {len(clusters)}")
    for cluster in clusters:
        print(f"- {cluster['name']} ({cluster['adapter_type']}): {cluster['node_count']} nodes, {cluster['gpu_count']} GPUs")
        
    # 提交任务到NVIDIA集群
    nvidia_task = controller.submit_task("NVIDIA Training Job", {
        "gpu_type": "nvidia",
        "min_memory": 40000  # 40GB
    })
    
    # 提交任务到Apple集群
    apple_task = controller.submit_task("Apple Inference Job", {
        "gpu_type": "apple",
        "min_memory": 16000  # 16GB
    })
    
    # 运行调度器
    controller.run_scheduler()
    
    # 检查任务状态
    print(f"NVIDIA Task Status: {controller.get_task_status(nvidia_task)}")
    print(f"Apple Task Status: {controller.get_task_status(apple_task)}")

if __name__ == "__main__":
    main()