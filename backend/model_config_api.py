from flask import Blueprint, jsonify, request
import uuid
from datetime import datetime

model_config_api = Blueprint('model_config_api', __name__)

# 模拟数据 - 模型配置
model_configs = [
    {
        "id": "1",
        "modelName": "llama-7b",
        "backend": "vllm",
        "modelPath": "/mnt/models/llama-7b",
        "cluster": "muxi集群",
        "image": "vllm_image:v3",
        "node": "node1",
        "gpuCount": 2,
        "memoryUsage": 24,
        "creator_id": "user1",
        "createTime": "2023-04-10T08:30:00Z"
    },
    {
        "id": "2",
        "modelName": "qwen-7b",
        "backend": "general",
        "modelPath": "/mnt/models/qwen-7b",
        "cluster": "A10集群",
        "image": "huggingface_image:v2",
        "node": "node2",
        "gpuCount": 1,
        "memoryUsage": 16,
        "creator_id": "user2",
        "createTime": "2023-04-12T10:15:00Z"
    },
    {
        "id": "3",
        "modelName": "chatglm-6b",
        "backend": "vilm",
        "modelPath": "/mnt/models/chatglm-6b",
        "cluster": "A100集群",
        "image": "vilm_image:v1",
        "node": "node3",
        "gpuCount": 1,
        "memoryUsage": 32,
        "creator_id": "user3",
        "createTime": "2023-04-15T14:45:00Z"
    }
]

# 模拟数据 - 集群
clusters = ["muxi集群", "A10集群", "A100集群"]

# 模拟数据 - 节点
nodes = ["node1", "node2", "node3", "node4", "node5", "node6"]

# 获取所有模型配置
@model_config_api.route('/api/model-configs', methods=['GET'])
def get_model_configs():
    return jsonify({
        "status": "success",
        "data": {
            "configs": model_configs
        }
    })

# 获取单个模型配置
@model_config_api.route('/api/model-configs/<id>', methods=['GET'])
def get_model_config(id):
    config = next((c for c in model_configs if c["id"] == id), None)
    if config:
        return jsonify({
            "status": "success",
            "data": config
        })
    return jsonify({
        "status": "error",
        "message": "模型配置不存在"
    }), 404

# 创建模型配置
@model_config_api.route('/api/model-configs', methods=['POST'])
def create_model_config():
    data = request.json
    new_config = {
        "id": str(uuid.uuid4()),
        "modelName": data.get("modelName"),
        "backend": data.get("backend"),
        "modelPath": data.get("modelPath"),
        "cluster": data.get("cluster"),
        "image": data.get("image"),
        "node": data.get("node"),
        "gpuCount": data.get("gpuCount"),
        "memoryUsage": data.get("memoryUsage"),
        "creator_id": data.get("creator_id"),
        "createTime": datetime.now().isoformat()
    }
    model_configs.append(new_config)
    return jsonify({
        "status": "success",
        "data": new_config
    }), 201

# 更新模型配置
@model_config_api.route('/api/model-configs/<id>', methods=['PUT'])
def update_model_config(id):
    config = next((c for c in model_configs if c["id"] == id), None)
    if not config:
        return jsonify({
            "status": "error",
            "message": "模型配置不存在"
        }), 404
    
    data = request.json
    for key, value in data.items():
        if key != "id" and key != "createTime":
            config[key] = value
    
    return jsonify({
        "status": "success",
        "data": config
    })

# 删除模型配置
@model_config_api.route('/api/model-configs/<id>', methods=['DELETE'])
def delete_model_config(id):
    global model_configs
    config = next((c for c in model_configs if c["id"] == id), None)
    if not config:
        return jsonify({
            "status": "error",
            "message": "模型配置不存在"
        }), 404
    
    model_configs = [c for c in model_configs if c["id"] != id]
    return jsonify({
        "status": "success",
        "message": "模型配置已删除"
    })

# 获取集群列表
@model_config_api.route('/api/clusters', methods=['GET'])
def get_clusters():
    return jsonify({
        "status": "success",
        "data": clusters
    })

# 获取节点列表
@model_config_api.route('/api/nodes', methods=['GET'])
def get_nodes():
    return jsonify({
        "status": "success",
        "data": nodes
    })
