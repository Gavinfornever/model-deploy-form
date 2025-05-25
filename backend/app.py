from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import random
import datetime
import json
import jwt
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
from auth_api import auth_api, generate_password_hash, check_password_hash, SECRET_KEY
from api_key_api import api_key_api

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
    required_fields = ['modelName', 'version', 'backend', 'image', 'cluster', 'node', 'gpuCount', 'memoryUsage', 'modelPath']
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
        'gpuCount': int(data['gpuCount']),  # 直接使用指定的GPU数量
        'memoryUsage': data['memoryUsage'],
        'modelPath': data['modelPath'],
        'description': data.get('description', ''),
        'creator_id': data.get('creator_id', 'anonymous'),
        'deployTime': datetime.datetime.now().isoformat(),
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
        'gpuCount': new_deployment['gpuCount'],  # 使用指定的GPU数量
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

if __name__ == '__main__':
    app.run(debug=True)
