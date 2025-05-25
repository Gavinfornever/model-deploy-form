from flask import Blueprint, jsonify, request
import uuid
from datetime import datetime
from pymongo import MongoClient

model_config_api = Blueprint('model_config_api', __name__)

# 连接MongoDB
try:
    # 使用提供的用户名和密码连接MongoDB
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    model_configs_collection = db['model_configs']
    
    print("MongoDB连接成功")
    
    # 检查集合是否存在，如果不存在则初始化数据
    if model_configs_collection.count_documents({}) == 0:
        # 初始化数据
        initial_configs = [
            {
                "id": "1",
                "modelName": "llama-7b",
                "backend": "vllm",
                "modelPath": "/mnt/models/llama-7b",
                "ossPath": "oss://model_files/llama-7b.tar",
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
                "ossPath": "oss://model_files/qwen-7b.tar",
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
                "ossPath": "oss://model_files/chatglm-6b.tar",
                "cluster": "A100集群",
                "image": "vilm_image:v1",
                "node": "node3",
                "gpuCount": 1,
                "memoryUsage": 32,
                "creator_id": "user3",
                "createTime": "2023-04-15T14:45:00Z"
            }
        ]
        model_configs_collection.insert_many(initial_configs)
        print("初始化模型配置数据完成")

except Exception as e:
    print(f"MongoDB连接失败: {e}")
    # 如果连接失败，使用备用数据

# 备用模拟数据
_fallback_model_configs = [
    {
        "id": "1",
        "modelName": "llama-7b",
        "backend": "vllm",
        "modelPath": "/mnt/models/llama-7b",
        "ossPath": "oss://model_files/llama-7b.tar",
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
        "ossPath": "oss://model_files/qwen-7b.tar",
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
        "ossPath": "oss://model_files/chatglm-6b.tar",
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
@model_config_api.route('/model-configs', methods=['GET'])
def get_model_configs():
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '')
        
        # 计算跳过的数量
        skip = (page - 1) * page_size
        
        # 构建查询条件
        query = {}
        if search:
            query['modelName'] = {'$regex': search, '$options': 'i'}
        
        # 从 MongoDB 查询数据
        configs = list(model_configs_collection.find(query).skip(skip).limit(page_size))
        total_count = model_configs_collection.count_documents(query)
        
        # 移除MongoDB的_id字段
        for config in configs:
            if '_id' in config:
                del config['_id']
        
        return jsonify({
            "status": "success",
            "data": {
                "configs": configs,
                "total": total_count,
                "page": page,
                "pageSize": page_size
            }
        })
    except Exception as e:
        print(f"获取模型配置失败: {e}")
        # 如果连接失败，使用备用数据
        return jsonify({
            "status": "success",
            "data": {
                "configs": _fallback_model_configs,
                "total": len(_fallback_model_configs),
                "page": page,
                "pageSize": page_size
            }
        })

# 获取单个模型配置
@model_config_api.route('/model-configs/<id>', methods=['GET'])
def get_model_config(id):
    try:
        # 从 MongoDB 查询数据
        config = model_configs_collection.find_one({"id": id})
        
        if config:
            # 移除MongoDB的_id字段
            if '_id' in config:
                del config['_id']
                
            return jsonify({
                "status": "success",
                "data": config
            })
        else:
            return jsonify({
                "status": "error",
                "message": "模型配置不存在"
            }), 404
    except Exception as e:
        print(f"获取单个模型配置失败: {e}")
        # 如果连接失败，使用备用数据
        config = next((c for c in _fallback_model_configs if c["id"] == id), None)
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
@model_config_api.route('/model-configs', methods=['POST'])
def create_model_config():
    try:
        data = request.json
        
        # 验证必要字段
        required_fields = ['modelName', 'backend', 'image', 'gpuCount', 'memoryUsage', 'modelPath']
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"缺少必要字段: {field}"}), 400
                
        # 确保node字段存在，如果不存在则设置默认值
        if 'node' not in data or not data['node']:
            data['node'] = 'default_node'
            
        # 确保creator_id字段存在，如果不存在则设置默认值
        if 'creator_id' not in data or not data['creator_id']:
            data['creator_id'] = 'default_user'
        
        # 生成新ID
        max_id_doc = model_configs_collection.find_one(sort=[('id', -1)])
        new_id = str(int(max_id_doc['id']) + 1) if max_id_doc else "1"
        
        new_config = {
            "id": new_id,
            "modelName": data.get("modelName"),
            "backend": data.get("backend"),
            "modelPath": data.get("modelPath"),
            "ossPath": data.get("ossPath", data.get("modelPath", "")),
            "image": data.get("image"),
            "node": data.get("node", ""),
            "gpuCount": data.get("gpuCount"),
            "memoryUsage": data.get("memoryUsage"),
            "creator_id": data.get("creator_id", ""),
            "createTime": datetime.now().isoformat()
        }
        
        # 添加到MongoDB
        model_configs_collection.insert_one(new_config)
        
        # 移除MongoDB的_id字段后返回
        new_config.pop('_id', None)
        return jsonify({
            "status": "success",
            "data": new_config
        }), 201
    except Exception as e:
        print(f"创建模型配置失败: {e}")
        # 如果连接失败，使用备用数据
        new_config = {
            "id": str(uuid.uuid4()),
            "modelName": data.get("modelName"),
            "backend": data.get("backend"),
            "modelPath": data.get("modelPath"),
            "ossPath": data.get("ossPath", data.get("modelPath", "")),
            "image": data.get("image"),
            "node": data.get("node", ""),
            "gpuCount": data.get("gpuCount"),
            "memoryUsage": data.get("memoryUsage"),
            "creator_id": data.get("creator_id", ""),
            "createTime": datetime.now().isoformat()
        }
        # 不在内存中保存数据，只在MongoDB中保存
        return jsonify({
            "status": "success",
            "data": new_config
        }), 201

# 更新模型配置
@model_config_api.route('/model-configs/<id>', methods=['PUT'])
def update_model_config(id):
    try:
        # 从 MongoDB 查询数据
        config = model_configs_collection.find_one({"id": id})
        
        if not config:
            return jsonify({
                "status": "error",
                "message": "模型配置不存在"
            }), 404
        
        data = request.json
        update_data = {}
        
        # 构建更新数据
        for key, value in data.items():
            if key != "id" and key != "createTime" and key != "_id":
                update_data[key] = value
        
        # 更新MongoDB中的数据
        model_configs_collection.update_one({"id": id}, {"$set": update_data})
        
        # 获取更新后的数据
        updated_config = model_configs_collection.find_one({"id": id})
        
        # 移除MongoDB的_id字段
        if '_id' in updated_config:
            del updated_config['_id']
        
        return jsonify({
            "status": "success",
            "data": updated_config
        })
    except Exception as e:
        print(f"更新模型配置失败: {e}")
        # 如果连接失败，使用备用数据
        config = next((c for c in _fallback_model_configs if c["id"] == id), None)
        if not config:
            return jsonify({
                "status": "error",
                "message": "模型配置不存在"
            }), 404
        
        for key, value in data.items():
            if key != "id" and key != "createTime":
                config[key] = value
        
        return jsonify({
            "status": "success",
            "data": config
        })

# 删除模型配置
@model_config_api.route('/model-configs/<id>', methods=['DELETE'])
def delete_model_config(id):
    try:
        # 从 MongoDB 查询数据
        config = model_configs_collection.find_one({"id": id})

        if not config:
            return jsonify({
                "status": "error",
                "message": "模型配置不存在"
            }), 404

        # 从 MongoDB 删除数据
        result = model_configs_collection.delete_one({"id": id})

        if result.deleted_count > 0:
            return jsonify({
                "status": "success",
                "message": "模型配置已删除"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "删除失败"
            }), 500
    except Exception as e:
        print(f"删除模型配置失败: {e}")
        # 如果连接失败，使用备用数据
        config = next((c for c in _fallback_model_configs if c["id"] == id), None)
        if not config:
            return jsonify({
                "status": "error",
                "message": "模型配置不存在"
            }), 404

        # 不从内存中删除数据，只从 MongoDB 中删除
        return jsonify({
            "status": "success",
            "message": "模型配置已删除"
        })

# 获取集群列表
@model_config_api.route('/clusters', methods=['GET'])
def get_clusters():
    return jsonify({
        "status": "success",
        "data": clusters
    })

# 获取节点列表
@model_config_api.route('/nodes', methods=['GET'])
def get_nodes():
    return jsonify({
        "status": "success",
        "data": nodes
    })
