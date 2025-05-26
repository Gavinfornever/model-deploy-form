from flask import Blueprint, request, jsonify
import uuid
import jwt
import datetime
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash

api_key_api = Blueprint('api_key_api', __name__)

# 导入密钥和MongoDB连接
from auth_api import SECRET_KEY
from pymongo import MongoClient

# 连接MongoDB
try:
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    users_collection = db['users']
    api_keys_collection = db['api_keys']
    print("MongoDB API密钥集合连接成功")
except Exception as e:
    print(f"MongoDB连接失败: {e}")

# 初始化API密钥数据
try:
    # 检查API密钥集合是否为空，如果为空则初始化数据
    if api_keys_collection.count_documents({}) == 0:
        initial_api_keys = [
            {
                "id": "key1",
                "name": "测试API密钥",
                "key": "sk-test-12345678901234567890123456789012",
                "scope": "只读",
                "user_id": "1",
                "created_at": "2025-05-01T10:00:00Z",
                "last_used": None
            }
        ]
        api_keys_collection.insert_many(initial_api_keys)
        print("API密钥数据初始化成功")
except Exception as e:
    print(f"API密钥数据初始化失败: {e}")

# 生成API密钥
def generate_api_key():
    # 生成一个32字符的随机字符串作为API密钥
    alphabet = string.ascii_letters + string.digits
    key = 'sk-' + ''.join(secrets.choice(alphabet) for _ in range(32))
    return key

# 验证JWT令牌
def verify_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except Exception as e:
        print(f"Token验证失败: {str(e)}")
        return None

# 获取API密钥列表
@api_key_api.route('/api-keys', methods=['GET'])
def get_api_keys():
    # 验证用户身份
    payload = verify_token()
    if not payload:
        return jsonify({"status": "error", "message": "未授权访问"}), 401
    
    user_id = payload.get('user_id')  # 注意：JWT中的字段是user_id而不是id
    # 打印完整的payload以检查字段
    print('\n\nJWT Payload:', payload)
    user_role = payload.get('role')
    
    try:
        # 管理员可以查看所有API密钥，普通用户只能查看自己的
        if user_role == '管理员':
            print('\n查询所有API密钥')
            keys_cursor = api_keys_collection.find({})
        else:
            query = {"user_id": user_id}
            print(f'\n查询用户 {user_id} 的API密钥, 查询条件: {query}')
            keys_cursor = api_keys_collection.find(query)
        
        # 将MongoDB文档转换为可JSON序列化的字典
        keys = []
        for key in keys_cursor:
            # 处理ObjectId
            if '_id' in key:
                key['_id'] = str(key['_id'])
            keys.append(key)
        
        print(f'\n查询结果: 找到 {len(keys)} 个API密钥')
        if keys:
            print('第一个API密钥:', keys[0])
    except Exception as e:
        print(f"API密钥获取失败: {str(e)}")
        return jsonify({"status": "error", "message": f"API密钥获取失败: {str(e)}"}), 500
    
    return jsonify({"status": "success", "data": keys}), 200

# 创建API密钥
@api_key_api.route('/api-keys', methods=['POST'])
def create_api_key():
    # 验证用户身份
    payload = verify_token()
    if not payload:
        return jsonify({"status": "error", "message": "未授权访问"}), 401
    
    data = request.json
    if not data or not data.get('name'):
        return jsonify({"status": "error", "message": "缺少必要参数"}), 400
    
    user_id = payload.get('id')
    
    # 生成API密钥
    key = generate_api_key()
    
    # 计算过期时间
    expiration = data.get('expiration', '永不过期')
    expires_at = None
    if expiration != '永不过期':
        days = int(expiration.replace('天', ''))
        expires_at = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    
    # 创建新的API密钥记录
    new_key = {
        "id": str(uuid.uuid4()),
        "name": data.get('name'),
        "key": key,
        "scope": data.get('scope', '只读'),
        "user_id": user_id,
        "created_at": datetime.datetime.now().isoformat(),
        "expires_at": expires_at,
        "last_used": None
    }
    
    api_keys.append(new_key)
    
    return jsonify({
        "status": "success", 
        "message": "API密钥创建成功", 
        "data": new_key
    }), 201

# 删除API密钥
@api_key_api.route('/api-keys/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    # 验证用户身份
    payload = verify_token()
    if not payload:
        return jsonify({"status": "error", "message": "未授权访问"}), 401
    
    user_id = payload.get('id')
    user_role = payload.get('role')
    
    # 查找要删除的API密钥
    key_index = None
    for i, key in enumerate(api_keys):
        if key['id'] == key_id:
            # 检查权限：只有密钥所有者或管理员可以删除
            if key['user_id'] == user_id or user_role == '管理员':
                key_index = i
                break
            else:
                return jsonify({"status": "error", "message": "无权删除此API密钥"}), 403
    
    if key_index is None:
        return jsonify({"status": "error", "message": "API密钥不存在"}), 404
    
    # 删除API密钥
    del api_keys[key_index]
    
    return jsonify({"status": "success", "message": "API密钥已删除"}), 200

# 重新生成API密钥
@api_key_api.route('/api-keys/<key_id>/regenerate', methods=['POST'])
def regenerate_api_key(key_id):
    # 验证用户身份
    payload = verify_token()
    if not payload:
        return jsonify({"status": "error", "message": "未授权访问"}), 401
    
    user_id = payload.get('id')
    user_role = payload.get('role')
    
    # 查找要重新生成的API密钥
    key_index = None
    for i, key in enumerate(api_keys):
        if key['id'] == key_id:
            # 检查权限：只有密钥所有者或管理员可以重新生成
            if key['user_id'] == user_id or user_role == '管理员':
                key_index = i
                break
            else:
                return jsonify({"status": "error", "message": "无权重新生成此API密钥"}), 403
    
    if key_index is None:
        return jsonify({"status": "error", "message": "API密钥不存在"}), 404
    
    # 生成新的API密钥
    new_key = generate_api_key()
    api_keys[key_index]['key'] = new_key
    
    return jsonify({
        "status": "success", 
        "message": "API密钥已重新生成", 
        "data": api_keys[key_index]
    }), 200

# 验证API密钥
@api_key_api.route('/api-keys/verify', methods=['POST'])
def verify_api_key():
    data = request.json
    if not data or not data.get('api_key'):
        return jsonify({"status": "error", "message": "缺少API密钥"}), 400
    
    api_key = data.get('api_key')
    
    # 查找API密钥
    key_info = None
    for key in api_keys:
        if key['key'] == api_key:
            key_info = key
            break
    
    if not key_info:
        return jsonify({"status": "error", "message": "无效的API密钥"}), 401
    
    # 检查密钥是否过期
    if key_info['expires_at']:
        expires_at = datetime.datetime.fromisoformat(key_info['expires_at'].replace('Z', '+00:00'))
        if datetime.datetime.now() > expires_at:
            return jsonify({"status": "error", "message": "API密钥已过期"}), 401
    
    # 更新最后使用时间
    key_info['last_used'] = datetime.datetime.now().isoformat()
    
    return jsonify({
        "status": "success", 
        "message": "API密钥有效", 
        "data": {
            "scope": key_info['scope'],
            "user_id": key_info['user_id']
        }
    }), 200
