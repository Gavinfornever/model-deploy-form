
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

# ====================== 适配器实现 ======================

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
            nodes.append(node)
            
        return nodes
    
    def get_gpu_info(self, node: NodeInfo) -> List[GPUInfo]:
        """获取NVIDIA GPU信息"""
        logger.info(f"Getting GPU info for NVIDIA node: {node.name}")
        
        # 在实际实现中，这里会通过SSH或API调用nvidia-smi
        # 为演示目的，我们模拟一些GPU
        gpus = []
        
        # 模拟调用nvidia-smi的结果
        try:
            # 实际实现会执行: ssh {node.ip} nvidia-smi --query-gpu=name,memory.total,uuid --format=csv,noheader
            # 这里模拟返回结果
            gpu_count = node.metadata.get("gpu_count", 4)  # 默认4个GPU
            
            for i in range(gpu_count):
                gpu = GPUInfo(
                    id=f"{node.id}-gpu-{i}",
                    name=f"NVIDIA RTX A6000",
                    memory_total=49152,  # 48GB
                    gpu_type=GPUType.NVIDIA,
                    compute_capability="8.6",
                    extra_info={
                        "driver_version": "535.129.03",
                        "cuda_version": "12.2"
                    }
                )
                gpus.append(gpu)
                
        except Exception as e:
            logger.error(f"Error getting NVIDIA GPU info: {e}")
            
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
            node = NodeInfo(
                id=node_config.get("id", str(uuid.uuid4())),
                name=node_config.get("name", f"apple-node-{len(nodes)}"),
                ip=node_config.get("ip", "127.0.0.1"),
                port=node_config.get("port", 22),
                status="unknown"
            )
            nodes.append(node)
            
        return nodes
    
    def get_gpu_info(self, node: NodeInfo) -> List[GPUInfo]:
        """获取Apple Silicon GPU信息"""
        logger.info(f"Getting GPU info for Apple Silicon node: {node.name}")
        
        # 在实际实现中，这里会通过SSH或API调用系统命令
        # 为演示目的，我们模拟一些GPU
        gpus = []
        
        try:
            # 实际实现会执行: ssh {node.ip} system_profiler SPDisplaysDataType
            # 这里模拟返回结果
            gpu_model = node.metadata.get("gpu_model", "M2 Max")
            
            # Apple Silicon通常只有一个集成GPU
            gpu = GPUInfo(
                id=f"{node.id}-gpu-0",
                name=f"Apple {gpu_model}",
                memory_total=32768,  # 32GB 统一内存
                gpu_type=GPUType.APPLE,
                extra_info={
                    "cores": 30,
                    "metal_version": "3.0"
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