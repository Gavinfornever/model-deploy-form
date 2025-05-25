#!/usr/bin/env python3
"""
清理Redis中的模型实例相关数据
"""

import redis
import json
import argparse

# 连接到Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def clean_model_instances():
    """清理模型实例相关数据"""
    print("开始清理Redis中的模型实例数据...")
    
    # 清理模型实例哈希表
    model_instances_keys = redis_client.keys("model_instances:*")
    if model_instances_keys:
        print(f"删除 {len(model_instances_keys)} 个模型实例键...")
        for key in model_instances_keys:
            redis_client.delete(key)
    
    # 清理models哈希表
    models_count = redis_client.hlen("models")
    if models_count > 0:
        print(f"删除 {models_count} 个模型记录...")
        redis_client.delete("models")
    
    # 清理集群-模型关联
    cluster_model_keys = redis_client.keys("cluster:*:models")
    if cluster_model_keys:
        print(f"删除 {len(cluster_model_keys)} 个集群-模型关联...")
        for key in cluster_model_keys:
            redis_client.delete(key)
    
    # 清理节点-模型关联
    node_model_keys = redis_client.keys("node:*:models")
    if node_model_keys:
        print(f"删除 {len(node_model_keys)} 个节点-模型关联...")
        for key in node_model_keys:
            redis_client.delete(key)
    
    # 清理在线/离线模型集合
    redis_client.delete("online_models")
    redis_client.delete("offline_models")
    print("已删除在线和离线模型集合")
    
    print("Redis清理完成！")

def clean_all_data():
    """清理所有数据（危险操作）"""
    print("警告：即将清理Redis中的所有数据！")
    confirm = input("确定要继续吗？(y/n): ")
    if confirm.lower() == 'y':
        redis_client.flushall()
        print("已清理Redis中的所有数据！")
    else:
        print("操作已取消")

def list_keys():
    """列出所有键"""
    print("Redis中的所有键:")
    for key in redis_client.keys("*"):
        print(f"- {key}")
        
        # 如果是哈希表，显示字段数量
        if redis_client.type(key) == "hash":
            count = redis_client.hlen(key)
            print(f"  (哈希表，包含 {count} 个字段)")
        
        # 如果是集合，显示成员数量
        elif redis_client.type(key) == "set":
            count = redis_client.scard(key)
            print(f"  (集合，包含 {count} 个成员)")

def main():
    parser = argparse.ArgumentParser(description="清理Redis中的数据")
    parser.add_argument("--all", action="store_true", help="清理所有数据（危险操作）")
    parser.add_argument("--list", action="store_true", help="列出所有键")
    parser.add_argument("--models", action="store_true", help="清理模型实例相关数据")
    
    args = parser.parse_args()
    
    if args.list:
        list_keys()
    elif args.all:
        clean_all_data()
    elif args.models:
        clean_model_instances()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
