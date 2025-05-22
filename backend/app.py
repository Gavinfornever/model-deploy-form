from flask import Flask, request, jsonify
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import random
import datetime
import jwt

# 导入API蓝图
from chat_api import chat_api
from image_api import image_api
from model_config_api import model_config_api
from auth_api import auth_api, users, generate_password_hash, check_password_hash, SECRET_KEY
from api_key_api import api_key_api

app = Flask(__name__)
CORS(app)

# 注册API蓝图
app.register_blueprint(chat_api, url_prefix='/api')
app.register_blueprint(image_api, url_prefix='/api')
app.register_blueprint(model_config_api, url_prefix='/api')
app.register_blueprint(auth_api, url_prefix='/api')
app.register_blueprint(api_key_api, url_prefix='/api')

# 模拟数据库，存储模型实例信息
model_instances = [
    {
        "id": "m0",
        "modelId": "qwen2.5-0.5b_vllm",
        "modelName": "qwen2.5-0.5b_vllm",
        "backend": "vllm",
        "server": "localhost",
        "port": "20093",
        "gpu": "0",
        "status": "running",
        "cluster": "local",
        "modelPath": "/models/qwen2.5-0.5b"
    },
    {
        "id": "m1",
        "modelId": "qwen_cpt_vilm",
        "modelName": "qwen_cpt_vllim",
        "backend": "vllim",
        "server": "10.31.29.02",
        "port": "21001",
        "gpu": "4",
        "status": "running",
        "cluster": "muxi",
        "modelPath": "/mnt/share/models/dataset_E_xy_14b"
    },
    {
        "id": "m2",
        "modelId": "selfmodel_vllm",
        "modelName": "selfmodel_vllm",
        "backend": "vllm",
        "server": "47.102.116.12",
        "port": "21001",
        "gpu": "0,1",
        "status": "stopped",
        "cluster": "A10服务器",
        "modelPath": "/mnt/share/models/xy.70b 30b fini.."
    },
    {
        "id": "m3",
        "modelId": "baai sim general",
        "modelName": "baai sim_general",
        "backend": "general",
        "server": "10.31.29.19",
        "port": "21010",
        "gpu": "3",
        "status": "running",
        "cluster": "muxi",
        "modelPath": "/mnt/share/models/tzy/BAAl-bge-ba.."
    },
    {
        "id": "m4",
        "modelId": "baai sim. general",
        "modelName": "baai sim general",
        "backend": "general",
        "server": "10.31.29.19",
        "port": "21011",
        "gpu": "0,1",
        "status": "running",
        "cluster": "A10服务器",
        "modelPath": "/mnt/share/models/tzy/BAAl-bge-ba.."
    },
    {
        "id": "m5",
        "modelId": "baai sim_general",
        "modelName": "baai sim_general",
        "backend": "general",
        "server": "10.31.29.19",
        "port": "21012",
        "gpu": "2",
        "status": "running",
        "cluster": "muxi",
        "modelPath": "/mnt/share/models/tzy/BAAl-bge-ba."
    },
    {
        "id": "m6",
        "modelId": "baai_sim_ general",
        "modelName": "baai_sim_general",
        "backend": "general",
        "server": "10.31.29.19",
        "port": "21013",
        "gpu": "8",
        "status": "stopped",
        "cluster": "A10服务器",
        "modelPath": "/mnt/share/models/tzy/BAAl-bge-ba."
    },
    {
        "id": "m7",
        "modelId": "qwen_comment vllm",
        "modelName": "qwen_comment vllm",
        "backend": "vllm",
        "server": "10.31.29.15",
        "port": "21004",
        "gpu": "5",
        "status": "running",
        "cluster": "muxi",
        "modelPath": "/mnt/share/models/comment v3/"
    },
    {
        "id": "m8",
        "modelId": "qwen datasetE yllm",
        "modelName": "qwen_datasetE vllm",
        "backend": "yllm",
        "server": "10.31.29.15",
        "port": "21005",
        "gpu": "6",
        "status": "running",
        "cluster": "A10服务器",
        "modelPath": "/mnt/share/models/dataset Exy.14b"
    },
    {
        "id": "m9",
        "modelId": "qwen14b__vllm",
        "modelName": "qwen14b_vllm",
        "backend": "vilm",
        "server": "10.31.29.15",
        "port": "21003",
        "gpu": "0",
        "status": "stopped",
        "cluster": "muxi",
        "modelPath": "/mnt/share/models/tzy/Qwen-14B-c."
    },
    {
        "id": "m10",
        "modelId": "embedding_generalgeneral",
        "modelName": "embedding_general",
        "backend": "general",
        "server": "10.31.29.15",
        "port": "21006",
        "gpu": "7",
        "status": "running",
        "cluster": "A10服务器",
        "modelPath": "/mnt/share/models/tzy/paraphrase-."
    }
]

@app.route('/api/deploy', methods=['POST'])
def deploy_model():
    data = request.json
    
    # 验证必要字段
    required_fields = ['modelName', 'version', 'backend', 'image', 'cluster', 'node', 'gpuIds', 'memoryUsage', 'modelPath']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'status': 'error', 
                'message': f'缺少必要字段: {field}'
            }), 400
    
    # 创建新的模型部署实例
    new_deployment = {
        'id': str(uuid.uuid4()),
        'modelName': data['modelName'],
        'version': data['version'],
        'backend': data['backend'],
        'image': data['image'],
        'cluster': data['cluster'],
        'node': data['node'],
        'gpuIds': data['gpuIds'],  # 使用指定的GPU序号
        'gpuCount': len(data['gpuIds']),  # 计算GPU数量
        'memoryUsage': data['memoryUsage'],
        'modelPath': data['modelPath'],
        'description': data.get('description', ''),
        'creator_id': data.get('creator_id', 'anonymous'),
        'deployTime': datetime.now().isoformat(),
        'status': 'pending',  # 初始状态为待处理
    }
    
    # 在实际应用中，这里会将部署请求发送到部署系统
    # 目前仅模拟部署过程
    
    # 将新部署添加到模型实例列表（模拟数据库操作）
    model_instances.append({
        'id': new_deployment['id'],
        'modelId': new_deployment['modelName'],
        'modelName': new_deployment['modelName'],
        'version': new_deployment['version'],
        'backend': new_deployment['backend'],
        'image': new_deployment['image'],
        'cluster': new_deployment['cluster'],
        'node': new_deployment['node'],
        'gpuIds': new_deployment['gpuIds'],  # 使用指定的GPU序号
        'gpuCount': new_deployment['gpuCount'],
        'memoryUsage': new_deployment['memoryUsage'],
        'status': 'running',  # 模拟部署成功后状态变为运行中
        'createTime': new_deployment['deployTime'],
        'creator': new_deployment['creator_id'],
        'description': new_deployment['description']
    })
    
    return jsonify({
        'status': 'success', 
        'message': '模型部署请求已提交',
        'data': new_deployment
    }), 201

# 用户管理API
@app.route('/api/users', methods=['GET'])
def get_users():
    # 验证JWT令牌
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            # 如果是管理员，返回所有用户，否则只返回自己的信息
            if payload.get('role') == '管理员':
                return jsonify({'status': 'success', 'data': users}), 200
            else:
                # 过滤掉密码字段
                user_data = next((user for user in users if user['id'] == payload.get('id')), None)
                if user_data:
                    user_copy = user_data.copy()
                    if 'password' in user_copy:
                        del user_copy['password']
                    return jsonify({'status': 'success', 'data': [user_copy]}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'无效的令牌: {str(e)}'}), 401
    
    # 为了便于测试，如果没有令牌也返回所有用户（实际生产环境应该返回401）
    safe_users = []
    for user in users:
        user_copy = user.copy()
        if 'password' in user_copy:
            del user_copy['password']
        safe_users.append(user_copy)
    return jsonify({'status': 'success', 'data': safe_users}), 200

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = next((user for user in users if user['id'] == user_id), None)
    if user:
        # 不返回密码字段
        user_copy = user.copy()
        if 'password' in user_copy:
            del user_copy['password']
        return jsonify({'status': 'success', 'data': user_copy}), 200
    return jsonify({'status': 'error', 'message': '用户不存在'}), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    if not data or 'username' not in data or 'email' not in data:
        return jsonify({'status': 'error', 'message': '缺少必要字段'}), 400
    
    # 检查用户名是否已存在
    if any(user['username'] == data['username'] for user in users):
        return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if any(user['email'] == data['email'] for user in users):
        return jsonify({'status': 'error', 'message': '邮箱已存在'}), 400
    
    # 生成唯一ID
    new_user = {
        'id': str(uuid.uuid4())[:8],
        'username': data['username'],
        'email': data['email'],
        'phone': data.get('phone', ''),
        'department': data.get('department', ''),
        'role': data.get('role', '普通用户'),
        'status': data.get('status', 'active'),
        'createTime': data.get('createTime', datetime.datetime.now().isoformat()),
        'lastLogin': None
    }
    
    # 处理密码字段
    if 'password' in data and data['password']:
        new_user['password'] = generate_password_hash(data['password'])
    else:
        # 如果没有提供密码，设置一个默认密码
        new_user['password'] = generate_password_hash('123456')
    
    users.append(new_user)
    
    # 不返回密码字段
    response_user = new_user.copy()
    if 'password' in response_user:
        del response_user['password']
    
    return jsonify({'status': 'success', 'data': response_user}), 201

@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    user_index = next((i for i, user in enumerate(users) if user['id'] == user_id), None)
    
    if user_index is None:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    
    # 检查用户名是否已存在（排除当前用户）
    if 'username' in data and data['username'] != users[user_index]['username']:
        if any(user['username'] == data['username'] for user in users if user['id'] != user_id):
            return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在（排除当前用户）
    if 'email' in data and data['email'] != users[user_index]['email']:
        if any(user['email'] == data['email'] for user in users if user['id'] != user_id):
            return jsonify({'status': 'error', 'message': '邮箱已存在'}), 400
    
    # 更新用户信息
    update_data = {
        'username': data.get('username', users[user_index]['username']),
        'email': data.get('email', users[user_index]['email']),
        'phone': data.get('phone', users[user_index].get('phone', '')),
        'department': data.get('department', users[user_index].get('department', '')),
        'role': data.get('role', users[user_index].get('role', '普通用户')),
        'status': data.get('status', users[user_index].get('status', 'active'))
    }
    
    # 处理密码字段
    if 'password' in data and data['password']:
        update_data['password'] = generate_password_hash(data['password'])
    
    users[user_index].update(update_data)
    
    # 不返回密码字段
    response_user = users[user_index].copy()
    if 'password' in response_user:
        del response_user['password']
    
    return jsonify({'status': 'success', 'data': response_user}), 200

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # 验证JWT令牌
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            # 只有管理员可以删除用户
            if payload.get('role') != '管理员':
                return jsonify({'status': 'error', 'message': '没有权限执行此操作'}), 403
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'无效的令牌: {str(e)}'}), 401
    
    global users
    initial_length = len(users)
    users = [user for user in users if user['id'] != user_id]
    
    if len(users) < initial_length:
        return jsonify({'status': 'success', 'message': '用户已删除'}), 200
    
    return jsonify({'status': 'error', 'message': '用户不存在'}), 404

# 模型实例管理API
@app.route('/api/models', methods=['GET'])
def get_models():
    # 获取查询参数
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    # 过滤模型
    filtered_models = model_instances
    if search:
        search = search.lower()
        filtered_models = [model for model in model_instances if 
                          search in model['modelName'].lower() or 
                          search in model['backend'].lower() or
                          search in model['server'].lower() or
                          search in model['gpu'].lower()]
    
    # 计算分页
    total = len(filtered_models)
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    paginated_models = filtered_models[start_idx:end_idx]
    
    return jsonify({
        'status': 'success',
        'data': {
            'models': paginated_models,
            'pagination': {
                'total': total,
                'current': page,
                'pageSize': page_size
            }
        }
    }), 200

@app.route('/api/models/<model_id>', methods=['GET'])
def get_model(model_id):
    model = next((model for model in model_instances if model['id'] == model_id), None)
    if model:
        return jsonify({'status': 'success', 'data': model}), 200
    return jsonify({'status': 'error', 'message': '模型不存在'}), 404

@app.route('/api/models/<model_id>/status', methods=['PUT'])
def update_model_status(model_id):
    data = request.json
    if not data or 'status' not in data:
        return jsonify({'status': 'error', 'message': '缺少状态信息'}), 400
    
    model_index = next((i for i, model in enumerate(model_instances) if model['id'] == model_id), None)
    if model_index is None:
        return jsonify({'status': 'error', 'message': '模型不存在'}), 404
    
    # 更新模型状态
    model_instances[model_index]['status'] = data['status']
    return jsonify({'status': 'success', 'data': model_instances[model_index]}), 200

# 模型配置数据
model_configs = [
    {
        "id": "conf1",
        "backend": "vllm",
        "modelPath": "/mnt/share/models/dataset_E_xy_14b",
        "cluster": "muxi",
        "image": "deploy_image:v3",
        "node": "node-01",
        "modelName": "qwen_cpt_vllim",
        "gpuCount": 4,
        "memoryUsage": 40,
        "creator_id": "1",
        "createTime": "2025-04-15 14:30:00"
    },
    {
        "id": "conf2",
        "backend": "vllm",
        "modelPath": "/mnt/share/models/xy.70b 30b fini..",
        "cluster": "A10服务器",
        "image": "deploy_image:v3",
        "node": "node-02",
        "modelName": "selfmodel_vllm",
        "gpuCount": 2,
        "memoryUsage": 24,
        "creator_id": "3",
        "createTime": "2025-04-18 09:15:00"
    },
    {
        "id": "conf3",
        "backend": "general",
        "modelPath": "/mnt/share/models/tzy/BAAl-bge-ba..",
        "cluster": "muxi",
        "image": "deploy_image:v3",
        "node": "node-03",
        "modelName": "baai sim_general",
        "gpuCount": 1,
        "memoryUsage": 16,
        "creator_id": "2",
        "createTime": "2025-04-20 11:45:00"
    },
    {
        "id": "conf4",
        "backend": "general",
        "modelPath": "/mnt/share/models/tzy/BAAl-bge-ba..",
        "cluster": "A10服务器",
        "image": "deploy_image:v3",
        "node": "node-04",
        "modelName": "baai sim general",
        "gpuCount": 2,
        "memoryUsage": 32,
        "creator_id": "1",
        "createTime": "2025-04-22 16:20:00"
    },
    {
        "id": "conf5",
        "backend": "vllm",
        "modelPath": "/mnt/share/models/comment v3/",
        "cluster": "muxi",
        "image": "deploy_image:v3",
        "node": "node-05",
        "modelName": "qwen_comment vllm",
        "gpuCount": 1,
        "memoryUsage": 12,
        "creator_id": "3",
        "createTime": "2025-04-25 10:30:00"
    }
]

# 模型配置API
@app.route('/api/model-configs', methods=['GET'])
def get_model_configs():
    # 获取查询参数
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    # 过滤模型配置
    filtered_configs = model_configs
    if search:
        search = search.lower()
        filtered_configs = [config for config in model_configs if 
                          search in config['modelName'].lower() or 
                          search in config['backend'].lower() or
                          search in config['cluster'].lower() or
                          search in config['node'].lower()]
    
    # 计算分页
    total = len(filtered_configs)
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    paginated_configs = filtered_configs[start_idx:end_idx]
    
    return jsonify({
        'status': 'success',
        'data': {
            'configs': paginated_configs,
            'pagination': {
                'total': total,
                'current': page,
                'pageSize': page_size
            }
        }
    }), 200

@app.route('/api/model-configs/<config_id>', methods=['GET'])
def get_model_config(config_id):
    config = next((config for config in model_configs if config['id'] == config_id), None)
    if config:
        return jsonify({'status': 'success', 'data': config}), 200
    return jsonify({'status': 'error', 'message': '配置不存在'}), 404

@app.route('/api/model-configs', methods=['POST'])
def create_model_config():
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': '缺少必要数据'}), 400
    
    required_fields = ['backend', 'modelPath', 'cluster', 'image', 'node', 'modelName', 'gpuCount', 'memoryUsage', 'creator_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'status': 'error', 'message': f'缺少必要字段: {field}'}), 400
    
    new_config = {
        'id': f'conf{len(model_configs) + 1}',
        'backend': data['backend'],
        'modelPath': data['modelPath'],
        'cluster': data['cluster'],
        'image': data['image'],
        'node': data['node'],
        'modelName': data['modelName'],
        'gpuCount': data['gpuCount'],
        'memoryUsage': data['memoryUsage'],
        'creator_id': data['creator_id'],
        'createTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    model_configs.append(new_config)
    return jsonify({'status': 'success', 'data': new_config}), 201

@app.route('/api/model-configs/<config_id>', methods=['PUT'])
def update_model_config(config_id):
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': '缺少必要数据'}), 400
    
    config_index = next((i for i, config in enumerate(model_configs) if config['id'] == config_id), None)
    if config_index is None:
        return jsonify({'status': 'error', 'message': '配置不存在'}), 404
    
    # 更新配置信息
    update_fields = ['backend', 'modelPath', 'cluster', 'image', 'node', 'modelName', 'gpuCount', 'memoryUsage']
    for field in update_fields:
        if field in data:
            model_configs[config_index][field] = data[field]
    
    return jsonify({'status': 'success', 'data': model_configs[config_index]}), 200

@app.route('/api/model-configs/<config_id>', methods=['DELETE'])
def delete_model_config(config_id):
    global model_configs
    initial_length = len(model_configs)
    model_configs = [config for config in model_configs if config['id'] != config_id]
    
    if len(model_configs) < initial_length:
        return jsonify({'status': 'success', 'message': '配置已删除'}), 200
    
    return jsonify({'status': 'error', 'message': '配置不存在'}), 404

# 获取集群列表
@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    clusters = list(set(config['cluster'] for config in model_configs))
    return jsonify({'status': 'success', 'data': clusters}), 200

# 获取节点列表
@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    nodes = list(set(config['node'] for config in model_configs))
    return jsonify({'status': 'success', 'data': nodes}), 200

# API使用量和Token使用量数据
usage_data = {
    'api_requests': {
        'total': 8923,
        'daily': 1456,
        'models': [
            {'name': 'qwen_cpt_vllim', 'requests': 3214, 'percentage': 36.0},
            {'name': 'selfmodel_vllm', 'requests': 2142, 'percentage': 24.0},
            {'name': 'baai sim_general', 'requests': 1562, 'percentage': 17.5},
            {'name': 'qwen_comment vllm', 'requests': 1160, 'percentage': 13.0},
            {'name': 'embedding_general', 'requests': 845, 'percentage': 9.5}
        ],
        'history': [
            {'date': '2025-04-30', 'count': 1034},
            {'date': '2025-05-01', 'count': 1156},
            {'date': '2025-05-02', 'count': 1078},
            {'date': '2025-05-03', 'count': 987},
            {'date': '2025-05-04', 'count': 1056},
            {'date': '2025-05-05', 'count': 1156},
            {'date': '2025-05-06', 'count': 1456}
        ]
    },
    'token_usage': {
        'total': 8945,
        'daily': 1256,
        'models': [
            {'name': 'qwen_cpt_vllim', 'tokens': 3245, 'percentage': 36.3},
            {'name': 'selfmodel_vllm', 'tokens': 2134, 'percentage': 23.9},
            {'name': 'baai sim_general', 'tokens': 1567, 'percentage': 17.5},
            {'name': 'qwen_comment vllm', 'tokens': 1123, 'percentage': 12.6},
            {'name': 'embedding_general', 'tokens': 876, 'percentage': 9.7}
        ],
        'history': [
            {'date': '2025-04-30', 'count': 1034},
            {'date': '2025-05-01', 'count': 1056},
            {'date': '2025-05-02', 'count': 1167},
            {'date': '2025-05-03', 'count': 1023},
            {'date': '2025-05-04', 'count': 987},
            {'date': '2025-05-05', 'count': 1123},
            {'date': '2025-05-06', 'count': 1256}
        ]
    }
}

# 获取API使用量和Token使用量数据
@app.route('/api/usage', methods=['GET'])
def get_usage_data():
    return jsonify({'status': 'success', 'data': usage_data}), 200

if __name__ == '__main__':
    app.run(debug=True)
