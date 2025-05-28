from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import uuid
import random
import datetime
import json
import jwt
import requests
from bson import ObjectId
from pymongo import MongoClient

# 自定义JSON编码器处理MongoDB的ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super(MongoJSONEncoder, self).default(obj)

# 导入API蓝图
from chat_api import chat_api
from image_api import image_api
from model_config_api import model_config_api
from model_deployment import model_instances_to_add
from auth_api import auth_api, generate_password_hash, check_password_hash, SECRET_KEY
from api_key_api import api_key_api
from model_deployment import model_deployment_api, init_model_deployment

# 连接MongoDB
try:
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    users_collection = db['users']
    
    # 检查用户集合是否为空，如果为空则初始化数据
    if users_collection.count_documents({}) == 0:
        # 初始化用户数据
        initial_users = [
            {
                "id": "1",
                "username": "admin",
                "password": generate_password_hash("admin123"),
                "email": "admin@example.com",
                "phone": "13800138000",
                "department": "技术部",
                "role": "管理员",
                "avatar": None,
                "status": "active",
                "createTime": "2025-01-01T08:00:00Z",
                "lastLogin": "2025-05-07T10:30:00Z"
            },
            {
                "id": "2",
                "username": "user",
                "password": generate_password_hash("user123"),
                "email": "user@example.com",
                "phone": "13900139000",
                "department": "产品部",
                "role": "普通用户",
                "avatar": None,
                "status": "active",
                "createTime": "2025-01-02T09:00:00Z",
                "lastLogin": "2025-05-06T15:45:00Z"
            }
        ]
        users_collection.insert_many(initial_users)
        print("用户数据初始化成功")
    
    print("MongoDB用户集合连接成功")
except Exception as e:
    print(f"MongoDB连接失败: {e}")

app = Flask(__name__)
CORS(app)

# 使用自定义JSON编码器
app.json_encoder = MongoJSONEncoder

# 注册API蓝图
app.register_blueprint(chat_api, url_prefix='/api')
app.register_blueprint(image_api, url_prefix='/api')
app.register_blueprint(model_config_api, url_prefix='/api')
app.register_blueprint(auth_api, url_prefix='/api')
app.register_blueprint(api_key_api, url_prefix='/api')
app.register_blueprint(model_deployment_api, url_prefix='')

# 注册模型路由器
try:
    from model_schedule.router import register_router
    register_router(app)
    print("模型路由器已成功注册")
except ImportError as e:
    print(f"模型路由器导入失败: {str(e)}")

# 初始化模型部署模块
init_model_deployment()

# 存储模型实例信息
model_instances = [
    # 真实的Mac-transformers模型实例
    {
        "id": "qwen-model-8076",
        "modelId": "qwen-model-8076",
        "modelName": "Qwen2.5-0.5B-Mac",
        "backend": "mac",
        "server": "localhost",
        "port": "8076",
        "gpu": "Apple Silicon",
        "status": "running",
        "cluster": "local",
        "modelPath": "/app/models/Qwen2.5-0.5B",
        "node": "localhost",
        "creator_name": "当前用户"
    },
    {
        "id": "qwen-model-8061",
        "modelId": "qwen-model-8061",
        "modelName": "Qwen2.5-0.5B-Mac",
        "backend": "mac",
        "server": "localhost",
        "port": "8061",
        "gpu": "Apple Silicon",
        "status": "running",
        "cluster": "local",
        "modelPath": "/app/models/Qwen2.5-0.5B",
        "node": "localhost",
        "creator_name": "当前用户"
    }
]

@app.route('/api/deploy', methods=['POST'])
def deploy_model():
    data = request.json
    
    # 打印接收到的请求数据
    print("\n\n接收到的部署请求数据:", data, "\n\n")
    
    # 验证必要字段
    required_fields = ['modelName', 'version', 'backend', 'cluster', 'node', 'gpuCount', 'memoryUsage', 'modelPath']
    
    # 检查镜像字段 - 支持 image 或 image_id
    if 'image' not in data and 'image_id' not in data:
        # 使用默认镜像
        data['image'] = 'transformers:apple-lite-v1'
        print("缺少镜像字段，使用默认镜像: transformers:apple-lite-v1")
    
    # 如果使用的是 image_id，将其转换为 image
    if 'image_id' in data and 'image' not in data:
        data['image'] = data['image_id']
        print(f"使用 image_id 作为 image: {data['image']}")
    
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
        'gpuCount': int(data['gpuCount']),
        'memoryUsage': data['memoryUsage'],
        'modelPath': data['modelPath'],
        'description': data.get('description', ''),
        'creator_id': data.get('creator_id', 'anonymous'),
        'deployTime': datetime.datetime.now().isoformat(),
        'status': 'pending',
    }
    
    # 根据系统类型选择部署方法
    import platform
    system_type = platform.system()
    
    if system_type == 'Darwin':  # macOS系统
        # 调用Mac部署模块
        deploy_data = {
            'model_name': data['modelName'],
            'model_path': data['modelPath'],
            'device': 'mps',  # 使用Apple GPU
            'port': 8000 + random.randint(1, 999),  # 随机分配端口
            'max_memory': data['memoryUsage'],
            'image': data['image']  # 传递镜像信息
        }
        
        # 发送请求到模型部署API（使用相对路径，避免端口冲突）
        from flask import url_for
        deploy_url = '/api/models/deploy'
        response = requests.post(
            f'http://localhost:5000{deploy_url}',
            json=deploy_data
        )
        
        if response.status_code == 200:
            result = response.json()
            # 更新部署信息
            new_deployment['status'] = 'running'  # 直接设置为运行中状态
            new_deployment['model_id'] = result.get('model_id')
            new_deployment['api_url'] = result.get('model_info', {}).get('api_url')
            
            # 将新部署添加到模型实例列表
            # 创建一个新的模型实例
            new_model_instance = {
                'id': new_deployment['id'],
                'modelId': new_deployment['modelName'],
                'modelName': new_deployment['modelName'],
                'version': new_deployment['version'],
                'backend': new_deployment['backend'],
                'image': new_deployment['image'],
                'cluster': new_deployment['cluster'],
                'node': new_deployment['node'],
                'gpuCount': new_deployment['gpuCount'],
                'memoryUsage': new_deployment['memoryUsage'],
                'status': 'running',  # 设置为运行中状态
                'createTime': new_deployment['deployTime'],
                'creator': new_deployment['creator_id'],
                'description': new_deployment['description'],
                'api_url': new_deployment.get('api_url'),
                'server': 'localhost',  # 添加服务器信息
                'port': str(deploy_data['port']),  # 添加端口信息
                'gpu': 'Apple Silicon'  # 添加GPU信息
            }
            
            # 检查是否已经存在该模型
            model_exists = False
            for i, model in enumerate(model_instances):
                if model.get('id') == new_model_instance['id']:
                    model_exists = True
                    model_instances[i] = new_model_instance  # 替换现有模型
                    break
            
            if not model_exists:
                model_instances.append(new_model_instance)
            
            return jsonify({
                'status': 'success', 
                'message': '模型部署请求已提交',
                'data': new_deployment
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': f'模型部署失败: {response.json().get("message", "未知错误")}'
            }), 500
    else:  # 其他系统（如Linux）
        # 保留原有的模拟部署逻辑
        model_instances.append({
            'id': new_deployment['id'],
            'modelId': new_deployment['modelName'],
            'modelName': new_deployment['modelName'],
            'version': new_deployment['version'],
            'backend': new_deployment['backend'],
            'image': new_deployment['image'],
            'cluster': new_deployment['cluster'],
            'node': new_deployment['node'],
            'gpuCount': new_deployment['gpuCount'],
            'memoryUsage': new_deployment['memoryUsage'],
            'status': 'running',  # 模拟部署成功后状态变为运行中
            'createTime': new_deployment['deployTime'],
            'creator': new_deployment['creator_id'],
            'description': new_deployment['description']
        })
        
        return jsonify({
            'status': 'success', 
            'message': '模型部署请求已提交（模拟模式）',
            'data': new_deployment
        }), 201

# 用户管理API
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        # 打印请求头
        print('\n\n请求头:', request.headers)
        print('Authorization:', request.headers.get('Authorization'))
        # 验证JWT令牌
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                print('Authorization header:', auth_header)
                token = auth_header.split(' ')[1]
                print('Token:', token)
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                    print('Payload:', payload)
                except Exception as jwt_error:
                    print('JWT解码错误:', str(jwt_error))
                    return jsonify({'status': 'error', 'message': f'JWT令牌无效: {str(jwt_error)}'}), 401
                # 所有用户都可以获取用户列表，但只有管理员可以看到敏感信息
                print('用户角色:', payload.get('role'))
                users = list(users_collection.find({}))
                # 手动移除密码字段和处理ObjectId
                for user in users:
                    if '_id' in user:
                        user['_id'] = str(user['_id'])
                    if 'password' in user:
                        del user['password']
                return jsonify({'status': 'success', 'data': users}), 200
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'无效的令牌: {str(e)}'}), 401
        
        # 如果没有令牌，返回401未授权错误
        return jsonify({'status': 'error', 'message': '未授权访问，请先登录'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'获取用户列表失败: {str(e)}'}), 500

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = users_collection.find_one({'id': user_id}, {'_id': 0, 'password': 0})
        if user:
            return jsonify({'status': 'success', 'data': user}), 200
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'获取用户信息失败: {str(e)}'}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        if not data or 'username' not in data or 'email' not in data:
            return jsonify({'status': 'error', 'message': '缺少必要字段'}), 400
        
        # 检查用户名是否已存在
        if users_collection.find_one({'username': data['username']}):
            return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
        
        # 检查邮箱是否已存在
        if users_collection.find_one({'email': data['email']}):
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
        
        # 将用户保存到MongoDB
        users_collection.insert_one(new_user)
        
        # 不返回密码字段
        response_user = new_user.copy()
        if 'password' in response_user:
            del response_user['password']
        
        return jsonify({'status': 'success', 'data': response_user}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'创建用户失败: {str(e)}'}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.json
        
        # 检查用户是否存在
        existing_user = users_collection.find_one({'id': user_id})
        if not existing_user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 检查用户名是否已存在（排除当前用户）
        if 'username' in data and data['username'] != existing_user['username']:
            if users_collection.find_one({'username': data['username'], 'id': {'$ne': user_id}}):
                return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
        
        # 检查邮箱是否已存在（排除当前用户）
        if 'email' in data and data['email'] != existing_user['email']:
            if users_collection.find_one({'email': data['email'], 'id': {'$ne': user_id}}):
                return jsonify({'status': 'error', 'message': '邮箱已存在'}), 400
        
        # 准备更新数据
        update_data = {}
        
        # 更新基本字段
        for field in ['username', 'email', 'phone', 'department', 'role', 'status']:
            if field in data:
                update_data[field] = data[field]
        
        # 处理密码字段
        if 'password' in data and data['password']:
            update_data['password'] = generate_password_hash(data['password'])
        
        # 更新MongoDB中的用户数据
        users_collection.update_one({'id': user_id}, {'$set': update_data})
        
        # 获取更新后的用户数据
        updated_user = users_collection.find_one({'id': user_id}, {'_id': 0, 'password': 0})
        
        return jsonify({'status': 'success', 'data': updated_user}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'更新用户失败: {str(e)}'}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
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
        
        # 检查用户是否存在
        existing_user = users_collection.find_one({'id': user_id})
        if not existing_user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 从 MongoDB 中删除用户
        result = users_collection.delete_one({'id': user_id})
        
        if result.deleted_count > 0:
            return jsonify({'status': 'success', 'message': '用户已删除'}), 200
        else:
            return jsonify({'status': 'error', 'message': '删除用户失败'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'删除用户失败: {str(e)}'}), 500

# 模型实例管理API
@app.route('/api/models', methods=['GET'])
def get_models():
    # 同步来自 model_deployment.py 的模型实例
    global model_instances
    if model_instances_to_add:
        for model in model_instances_to_add:
            # 检查模型是否已经存在
            exists = False
            for existing_model in model_instances:
                if existing_model.get('id') == model.get('id'):
                    # 更新现有模型
                    existing_model.update(model)
                    exists = True
                    break
            
            # 如果不存在，添加新模型
            if not exists:
                model_instances.append(model)
        
        # 清空待添加列表
        model_instances_to_add.clear()
    
    # 获取查询参数
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    # 过滤模型
    filtered_models = model_instances
    if search:
        search = search.lower()
        filtered_models = [model for model in model_instances if 
                          search in model.get('modelName', '').lower() or 
                          search in model.get('backend', '').lower() or
                          search in model.get('server', '').lower() or
                          search in model.get('gpu', '').lower()]
    
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

# 模型配置数据和API已移至model_config_api.py
# 使用MongoDB进行持久化存储

# 获取集群列表
# @app.route('/api/clusters', methods=['GET'])
# def get_clusters():
#     clusters = list(set(config['cluster'] for config in model_configs))
#     return jsonify({'status': 'success', 'data': clusters}), 200

# 获取节点列表
# @app.route('/api/nodes', methods=['GET'])
# def get_nodes():
#     nodes = list(set(config['node'] for config in model_configs))
#     return jsonify({'status': 'success', 'data': nodes}), 200

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

# 获取Docker中运行的模型实例
@app.route('/api/models/docker', methods=['GET'])
def get_docker_models():
    try:
        # 执行 docker ps 命令获取运行中的容器
        import subprocess
        cmd = "docker ps --filter 'name=qwen-model-' --format '{{.Names}},{{.Ports}},{{.Image}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({
                'status': 'error',
                'message': f'获取Docker容器列表失败: {result.stderr}'
            }), 500
        
        # 解析输出结果
        docker_models = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split(',')
            if len(parts) < 2:
                continue
            
            container_name = parts[0]
            ports_info = parts[1]
            
            # 提取端口信息
            import re
            port_match = re.search(r'0.0.0.0:(\d+)->8000/tcp', ports_info)
            if not port_match:
                continue
            
            port = port_match.group(1)
            
            # 从容器名称中提取模型名称
            model_id = container_name
            model_name = container_name.replace('-', ' ').title()
            
            # 提取镜像信息
            image_info = parts[2] if len(parts) > 2 else "transformers:apple-lite-v1"
            
            # 创建模型实例
            model_instance = {
                "id": model_id,
                "modelId": model_id,
                "modelName": model_name,
                "backend": "mac",
                "server": "localhost",
                "port": port,
                "gpu": "Apple Silicon",
                "status": "running",
                "cluster": "local",
                "node": "localhost",
                "creator_name": "当前用户",
                "image": image_info,
                "image_id": image_info
            }
            
            docker_models.append(model_instance)
        
        # 更新全局模型实例列表
        global model_instances
        
        # 删除现有的Mac部署模型
        model_instances = [m for m in model_instances if not (m.get('backend') == 'mac' and m.get('id', '').startswith('qwen-model-'))]
        
        # 添加新发现的Docker模型
        model_instances.extend(docker_models)
        
        return jsonify({
            'status': 'success',
            'data': docker_models
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取Docker模型列表失败: {str(e)}'
        }), 500

# 流式聊天API
@app.route('/api/chat/stream', methods=['GET'])
def chat_stream():
    model_id = request.args.get('model_id')
    message = request.args.get('message')
    
    if not model_id or not message:
        return jsonify({'status': 'error', 'message': '缺少模型ID或消息内容'}), 400
    
    # 查找模型实例
    model = next((m for m in model_instances if m['id'] == model_id), None)
    if not model:
        return jsonify({'status': 'error', 'message': '模型不存在'}), 404
    
    # 检查模型状态
    if model.get('status') != 'running':
        return jsonify({'status': 'error', 'message': '模型未运行'}), 400
    
    # 获取模型API URL
    port = model.get('port')
    if not port:
        return jsonify({'status': 'error', 'message': '模型端口未知'}), 500
    
    def generate():
        import time
        
        # 发送SSE头部
        yield "data: {\"text\": \"正在连接模型...\"}\n\n"
        
        try:
            # 构建请求URL - 使用正确的流式API端点
            api_url = f"http://localhost:{port}/generate/stream"
            
            print(f"发送请求到: {api_url}, 消息: {message}")
            
            # 发送请求到模型API，并启用流式传输
            response = requests.post(
                api_url,
                json={
                    "prompt": message,
                    "max_length": 100,  # 减少max_length加快生成速度
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                stream=True,  # 启用流式传输
                timeout=30  # 超时时间
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"模型API返回错误: {response.status_code}"
                print(error_msg)
                yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # 直接转发流式响应
            for line in response.iter_lines():
                if line:
                    try:
                        # 解析每行数据
                        line_text = line.decode('utf-8')
                        print(f"收到流式响应: {line_text}")
                        
                        # 直接转发原始数据给前端
                        yield f"data: {line_text}\n\n"
                        
                        # 检查是否是最后一条消息
                        try:
                            json_data = json.loads(line_text)
                            if json_data.get('done', False) is True:  # 明确检查done是否为True
                                print("检测到流式响应结束")
                        except json.JSONDecodeError as e:
                            print(f"JSON解析错误: {str(e)}, 原始数据: {line_text}")
                    except Exception as e:
                        print(f"处理流式响应行时发生错误: {str(e)}")
            
            # 确保发送结束标记
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_msg = f"连接模型API时发生错误: {str(e)}"
            print(error_msg)
            yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
            yield "data: [DONE]\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
