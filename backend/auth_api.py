from flask import Blueprint, jsonify, request
import uuid
import jwt
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

auth_api = Blueprint('auth_api', __name__)

# 模拟用户数据
users = [
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

# 密钥，实际应用中应该存储在环境变量中
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')

# 注册接口
@auth_api.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    phone = data.get('phone')
    department = data.get('department')
    
    # 验证必要字段
    if not username or not password or not email:
        return jsonify({
            "status": "error",
            "message": "用户名、密码和邮箱不能为空"
        }), 400
    
    # 检查用户名是否已存在
    if any(u["username"] == username for u in users):
        return jsonify({
            "status": "error",
            "message": "用户名已存在"
        }), 400
    
    # 检查邮箱是否已存在
    if any(u["email"] == email for u in users):
        return jsonify({
            "status": "error",
            "message": "邮箱已存在"
        }), 400
    
    # 创建新用户
    new_user = {
        "id": str(uuid.uuid4())[:8],
        "username": username,
        "password": generate_password_hash(password),
        "email": email,
        "phone": phone or "",
        "department": department or "",
        "role": "普通用户",  # 默认角色
        "avatar": None,
        "status": "active",
        "createTime": datetime.datetime.now().isoformat(),
        "lastLogin": None
    }
    
    # 添加到用户列表
    users.append(new_user)
    
    # 返回用户信息（不包含密码）
    user_info = {k: v for k, v in new_user.items() if k != 'password'}
    
    return jsonify({
        "status": "success",
        "message": "注册成功",
        "data": user_info
    }), 201

# 登录接口
@auth_api.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            "status": "error",
            "message": "用户名和密码不能为空"
        }), 400
    
    user = next((u for u in users if u["username"] == username), None)
    
    if not user or not check_password_hash(user["password"], password):
        return jsonify({
            "status": "error",
            "message": "用户名或密码错误"
        }), 401
    
    # 更新最后登录时间
    user["lastLogin"] = datetime.datetime.now().isoformat()
    
    # 创建JWT令牌
    token = jwt.encode({
        'user_id': user["id"],
        'exp': datetime.datetime.now() + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm='HS256')
    
    # 返回用户信息和令牌（不包含密码）
    user_info = {k: v for k, v in user.items() if k != 'password'}
    
    return jsonify({
        "status": "success",
        "message": "登录成功",
        "data": {
            "user": user_info,
            "token": token
        }
    })

# 获取当前用户信息
@auth_api.route('/api/me', methods=['GET'])
def get_current_user():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "status": "error",
            "message": "未提供有效的认证令牌"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']
        
        user = next((u for u in users if u["id"] == user_id), None)
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "用户不存在"
            }), 404
        
        # 返回用户信息（不包含密码）
        user_info = {k: v for k, v in user.items() if k != 'password'}
        
        return jsonify({
            "status": "success",
            "data": user_info
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({
            "status": "error",
            "message": "认证令牌已过期"
        }), 401
    except jwt.InvalidTokenError:
        return jsonify({
            "status": "error",
            "message": "无效的认证令牌"
        }), 401

# 修改密码
@auth_api.route('/api/users/<id>/change-password', methods=['POST'])
def change_password(id):
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "status": "error",
            "message": "未提供有效的认证令牌"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        token_user_id = payload['user_id']
        
        # 只能修改自己的密码
        if token_user_id != id:
            return jsonify({
                "status": "error",
                "message": "无权修改其他用户的密码"
            }), 403
        
        user = next((u for u in users if u["id"] == id), None)
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "用户不存在"
            }), 404
        
        data = request.json
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        
        if not old_password or not new_password:
            return jsonify({
                "status": "error",
                "message": "旧密码和新密码不能为空"
            }), 400
        
        if not check_password_hash(user["password"], old_password):
            return jsonify({
                "status": "error",
                "message": "旧密码错误"
            }), 400
        
        # 更新密码
        user["password"] = generate_password_hash(new_password)
        
        return jsonify({
            "status": "success",
            "message": "密码修改成功"
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({
            "status": "error",
            "message": "认证令牌已过期"
        }), 401
    except jwt.InvalidTokenError:
        return jsonify({
            "status": "error",
            "message": "无效的认证令牌"
        }), 401

# 上传头像
@auth_api.route('/api/users/avatar', methods=['POST'])
def upload_avatar():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            "status": "error",
            "message": "未提供有效的认证令牌"
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']
        
        user = next((u for u in users if u["id"] == user_id), None)
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "用户不存在"
            }), 404
        
        # 模拟头像上传，实际应用中应该处理文件上传
        # 这里简单返回一个模拟的头像URL
        avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={user['username']}"
        
        # 更新用户头像
        user["avatar"] = avatar_url
        
        return jsonify({
            "status": "success",
            "message": "头像上传成功",
            "data": {
                "url": avatar_url
            }
        })
    
    except jwt.ExpiredSignatureError:
        return jsonify({
            "status": "error",
            "message": "认证令牌已过期"
        }), 401
    except jwt.InvalidTokenError:
        return jsonify({
            "status": "error",
            "message": "无效的认证令牌"
        }), 401
