#!/usr/bin/env python3
"""
GPU资源调度策略
提供多种GPU资源调度算法，用于在集群内分配GPU资源
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gpu_scheduler")

# 导入数据模型
from ClusterRegister import GPUInfo, NodeInfo, ClusterInfo

@dataclass
class GPUAllocation:
    """GPU分配结果"""
    success: bool = False
    allocation: Dict[str, List[str]] = None  # {node_id: [gpu_ids]}
    message: str = ""

class GPUScheduler:
    """GPU调度器基类"""
    
    def allocate_gpus(self, cluster: ClusterInfo, gpu_count: int, memory_required: int) -> GPUAllocation:
        """
        分配GPU资源的抽象方法
        
        Args:
            cluster: 集群信息
            gpu_count: 需要的GPU数量
            memory_required: 每个GPU需要的显存(MB)
            
        Returns:
            GPUAllocation: 分配结果
        """
        raise NotImplementedError("Subclasses must implement this method")

class SingleNodeFirstScheduler(GPUScheduler):
    """单节点优先调度器
    
    优先在单个节点上分配所有GPU，如果无法满足，则尝试跨节点分配
    """
    
    def allocate_gpus(self, cluster: ClusterInfo, gpu_count: int, memory_required: int) -> GPUAllocation:
        """
        优先在单节点分配GPU，如无法满足则跨节点分配
        
        Args:
            cluster: 集群信息
            gpu_count: 需要的GPU数量
            memory_required: 每个GPU需要的显存(MB)
            
        Returns:
            GPUAllocation: 分配结果
        """
        logger.info(f"尝试分配 {gpu_count} 个GPU，每个至少 {memory_required}MB 显存")
        
        # 1. 首先尝试在单个节点上分配所有GPU
        for node in cluster.nodes:
            if node.status != "online":
                continue
                
            # 找出该节点上所有满足内存要求的GPU
            available_gpus = []
            for gpu in node.gpus:
                # 这里假设GPU的memory_total表示总显存，实际使用时可能需要考虑已用显存
                if gpu.memory_total >= memory_required:
                    available_gpus.append(gpu)
            
            # 如果该节点上可用GPU数量足够，直接分配
            if len(available_gpus) >= gpu_count:
                # 按照显存大小排序（从大到小），优先使用显存大的GPU
                # 实际使用时可能需要考虑GPU利用率，这里简化处理
                available_gpus.sort(key=lambda g: g.memory_total, reverse=True)
                selected_gpus = available_gpus[:gpu_count]
                
                return GPUAllocation(
                    success=True,
                    allocation={node.id: [gpu.id for gpu in selected_gpus]},
                    message=f"在节点 {node.name} 上成功分配 {gpu_count} 个GPU"
                )
        
        # 2. 如果没有单个节点能满足需求，尝试跨节点分配
        allocation = {}
        remaining_gpus = gpu_count
        
        # 按照节点上可用GPU数量排序（从多到少），尽量减少跨节点数量
        sorted_nodes = []
        for node in cluster.nodes:
            if node.status != "online":
                continue
                
            available_gpu_count = sum(1 for gpu in node.gpus if gpu.memory_total >= memory_required)
            sorted_nodes.append((node, available_gpu_count))
        
        sorted_nodes.sort(key=lambda x: x[1], reverse=True)
        
        for node, _ in sorted_nodes:
            if remaining_gpus <= 0:
                break
                
            available_gpus = [gpu for gpu in node.gpus if gpu.memory_total >= memory_required]
            available_gpus.sort(key=lambda g: g.memory_total, reverse=True)
            
            # 决定在这个节点上分配多少GPU
            gpus_to_allocate = min(len(available_gpus), remaining_gpus)
            if gpus_to_allocate > 0:
                selected_gpus = available_gpus[:gpus_to_allocate]
                allocation[node.id] = [gpu.id for gpu in selected_gpus]
                remaining_gpus -= gpus_to_allocate
        
        # 如果无法满足所有GPU需求，返回失败
        if remaining_gpus > 0:
            return GPUAllocation(
                success=False,
                message=f"无法满足GPU需求，还需要 {remaining_gpus} 个GPU"
            )
        
        return GPUAllocation(
            success=True,
            allocation=allocation,
            message=f"跨节点分配了 {gpu_count} 个GPU，涉及 {len(allocation)} 个节点"
        )

class MemoryOptimizedScheduler(GPUScheduler):
    """显存优化调度器
    
    优先分配剩余显存最大的GPU，适合大模型部署
    """
    
    def allocate_gpus(self, cluster: ClusterInfo, gpu_count: int, memory_required: int) -> GPUAllocation:
        """
        优先分配剩余显存最大的GPU
        
        Args:
            cluster: 集群信息
            gpu_count: 需要的GPU数量
            memory_required: 每个GPU需要的显存(MB)
            
        Returns:
            GPUAllocation: 分配结果
        """
        logger.info(f"尝试分配 {gpu_count} 个GPU，每个至少 {memory_required}MB 显存，优化显存使用")
        
        # 收集所有满足内存要求的GPU
        all_available_gpus = []
        for node in cluster.nodes:
            if node.status != "online":
                continue
                
            for gpu in node.gpus:
                if gpu.memory_total >= memory_required:
                    # 记录节点信息和GPU信息
                    all_available_gpus.append((node, gpu))
        
        # 按照显存大小排序（从大到小）
        all_available_gpus.sort(key=lambda x: x[1].memory_total, reverse=True)
        
        # 如果可用GPU数量不足，返回失败
        if len(all_available_gpus) < gpu_count:
            return GPUAllocation(
                success=False,
                message=f"可用GPU数量不足，需要 {gpu_count} 个，但只有 {len(all_available_gpus)} 个"
            )
        
        # 选择显存最大的GPU
        selected_gpus = all_available_gpus[:gpu_count]
        
        # 按节点组织分配结果
        allocation = {}
        for node, gpu in selected_gpus:
            if node.id not in allocation:
                allocation[node.id] = []
            allocation[node.id].append(gpu.id)
        
        return GPUAllocation(
            success=True,
            allocation=allocation,
            message=f"成功分配 {gpu_count} 个GPU，优化显存使用"
        )

class UtilizationAwareScheduler(GPUScheduler):
    """利用率感知调度器
    
    优先分配利用率低的GPU，平衡集群负载
    """
    
    def allocate_gpus(self, cluster: ClusterInfo, gpu_count: int, memory_required: int) -> GPUAllocation:
        """
        优先分配利用率低的GPU
        
        Args:
            cluster: 集群信息
            gpu_count: 需要的GPU数量
            memory_required: 每个GPU需要的显存(MB)
            
        Returns:
            GPUAllocation: 分配结果
        """
        logger.info(f"尝试分配 {gpu_count} 个GPU，每个至少 {memory_required}MB 显存，考虑GPU利用率")
        
        # 收集所有满足内存要求的GPU
        all_available_gpus = []
        for node in cluster.nodes:
            if node.status != "online":
                continue
                
            for gpu in node.gpus:
                if gpu.memory_total >= memory_required:
                    # 记录节点信息和GPU信息
                    # 这里假设GPU的extra_info中有utilization字段表示利用率
                    # 如果没有，默认为0
                    utilization = gpu.extra_info.get("utilization", 0)
                    all_available_gpus.append((node, gpu, utilization))
        
        # 按照利用率排序（从低到高）
        all_available_gpus.sort(key=lambda x: x[2])
        
        # 如果可用GPU数量不足，返回失败
        if len(all_available_gpus) < gpu_count:
            return GPUAllocation(
                success=False,
                message=f"可用GPU数量不足，需要 {gpu_count} 个，但只有 {len(all_available_gpus)} 个"
            )
        
        # 选择利用率最低的GPU
        selected_gpus = all_available_gpus[:gpu_count]
        
        # 按节点组织分配结果
        allocation = {}
        for node, gpu, _ in selected_gpus:
            if node.id not in allocation:
                allocation[node.id] = []
            allocation[node.id].append(gpu.id)
        
        return GPUAllocation(
            success=True,
            allocation=allocation,
            message=f"成功分配 {gpu_count} 个GPU，优化GPU利用率"
        )

class GPUResourceManager:
    """GPU资源管理器
    
    管理GPU资源的分配和释放
    """
    
    def __init__(self):
        self.scheduler = SingleNodeFirstScheduler()  # 默认使用单节点优先调度器
        self.allocations = {}  # {model_id: GPUAllocation}
    
    def set_scheduler(self, scheduler: GPUScheduler):
        """设置调度器"""
        self.scheduler = scheduler
    
    def allocate_gpus(self, cluster: ClusterInfo, model_id: str, gpu_count: int, memory_required: int) -> GPUAllocation:
        """
        为模型分配GPU资源
        
        Args:
            cluster: 集群信息
            model_id: 模型ID
            gpu_count: 需要的GPU数量
            memory_required: 每个GPU需要的显存(MB)
            
        Returns:
            GPUAllocation: 分配结果
        """
        # 如果模型已有分配，先释放
        if model_id in self.allocations:
            self.release_gpus(model_id)
        
        # 分配GPU
        allocation = self.scheduler.allocate_gpus(cluster, gpu_count, memory_required)
        
        # 如果分配成功，记录分配情况
        if allocation.success:
            self.allocations[model_id] = allocation
            logger.info(f"模型 {model_id} 成功分配GPU: {allocation.allocation}")
        else:
            logger.warning(f"模型 {model_id} 分配GPU失败: {allocation.message}")
        
        return allocation
    
    def release_gpus(self, model_id: str) -> bool:
        """
        释放模型的GPU资源
        
        Args:
            model_id: 模型ID
            
        Returns:
            bool: 是否成功释放
        """
        if model_id not in self.allocations:
            logger.warning(f"模型 {model_id} 没有GPU分配记录")
            return False
        
        allocation = self.allocations[model_id]
        logger.info(f"释放模型 {model_id} 的GPU资源: {allocation.allocation}")
        
        # 释放资源
        del self.allocations[model_id]
        return True
    
    def get_allocation(self, model_id: str) -> Optional[GPUAllocation]:
        """获取模型的GPU分配情况"""
        return self.allocations.get(model_id)
    
    def get_all_allocations(self) -> Dict[str, GPUAllocation]:
        """获取所有模型的GPU分配情况"""
        return self.allocations.copy()


# 创建全局GPU资源管理器实例
gpu_resource_manager = GPUResourceManager()

# 示例使用
def example_usage():
    """示例使用"""
    from ClusterRegister import ClusterInfo, NodeInfo, GPUInfo, GPUType
    
    # 创建一个测试集群
    cluster = ClusterInfo(
        id="test-cluster",
        name="测试集群",
        adapter_type="nvidia"
    )
    
    # 添加节点1，有4张GPU
    node1 = NodeInfo(
        id="node1",
        name="节点1",
        ip="10.0.0.1",
        port=22,
        status="online"
    )
    node1.gpus = [
        GPUInfo(id="0", name="Tesla V100", memory_total=16384, gpu_type=GPUType.NVIDIA),
        GPUInfo(id="1", name="Tesla V100", memory_total=16384, gpu_type=GPUType.NVIDIA),
        GPUInfo(id="2", name="Tesla V100", memory_total=16384, gpu_type=GPUType.NVIDIA),
        GPUInfo(id="3", name="Tesla V100", memory_total=16384, gpu_type=GPUType.NVIDIA),
    ]
    
    # 添加节点2，有2张GPU
    node2 = NodeInfo(
        id="node2",
        name="节点2",
        ip="10.0.0.2",
        port=22,
        status="online"
    )
    node2.gpus = [
        GPUInfo(id="0", name="Tesla A100", memory_total=40960, gpu_type=GPUType.NVIDIA),
        GPUInfo(id="1", name="Tesla A100", memory_total=40960, gpu_type=GPUType.NVIDIA),
    ]
    
    # 将节点添加到集群
    cluster.nodes = [node1, node2]
    
    # 创建GPU资源管理器
    manager = GPUResourceManager()
    
    # 使用单节点优先调度器
    manager.set_scheduler(SingleNodeFirstScheduler())
    
    # 分配GPU
    allocation1 = manager.allocate_gpus(cluster, "model1", 2, 15000)
    print(f"Model1 allocation: {allocation1}")
    
    # 使用显存优化调度器
    manager.set_scheduler(MemoryOptimizedScheduler())
    
    # 分配GPU
    allocation2 = manager.allocate_gpus(cluster, "model2", 3, 15000)
    print(f"Model2 allocation: {allocation2}")
    
    # 使用利用率感知调度器
    manager.set_scheduler(UtilizationAwareScheduler())
    
    # 分配GPU
    allocation3 = manager.allocate_gpus(cluster, "model3", 1, 30000)
    print(f"Model3 allocation: {allocation3}")
    
    # 释放资源
    manager.release_gpus("model1")
    manager.release_gpus("model2")
    manager.release_gpus("model3")

if __name__ == "__main__":
    example_usage()
