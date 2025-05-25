from flask import Blueprint, jsonify, request
import uuid
import jwt
import datetime
import os
import json
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient

# 自定义JSON编码器处理MongoDB的ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MongoJSONEncoder, self).default(obj)

# 辅助函数：将MongoDB文档转换为可JSON序列化的字典
def mongo_to_dict(doc):
    if doc is None:
        return None
    doc_dict = {}
    for k, v in doc.items():
        if k == '_id':
            doc_dict['_id'] = str(v)
        else:
            doc_dict[k] = v
    return doc_dict

auth_api = Blueprint('auth_api', __name__)

# 连接MongoDB
try:
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    users_collection = db['users']
    print("MongoDB用户集合连接成功")
except Exception as e:
    print(f"MongoDB连接失败: {e}")

# 密钥，实际应用中应该存储在环境变量中
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')

# 注册接口
@auth_api.route('/register', methods=['POST'])
def register():
    try:
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
        if users_collection.find_one({"username": username}):
            return jsonify({
                "status": "error",
                "message": "用户名已存在"
            }), 400
        
        # 检查邮箱是否已存在
        if users_collection.find_one({"email": email}):
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
        
        # 添加到MongoDB
        users_collection.insert_one(new_user)
        
        # 删除密码字段
        new_user.pop('password', None)
        
        # 返回用户信息（不包含_id）
        user_info = new_user
        
        return jsonify({
            "status": "success",
            "message": "注册成功",
            "data": user_info
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"注册失败: {str(e)}"
        }), 500

# 登录接口
@auth_api.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                "status": "error",
                "message": "用户名和密码不能为空"
            }), 400
        
        # 从 MongoDB 中查找用户
        user = users_collection.find_one({"username": username})
        
        if not user or not check_password_hash(user["password"], password):
            return jsonify({
                "status": "error",
                "message": "用户名或密码错误"
            }), 401
        
        # 更新最后登录时间
        last_login_time = datetime.datetime.now().isoformat()
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"lastLogin": last_login_time}}
        )
        user["lastLogin"] = last_login_time
        
        # 创建JWT令牌
        token = jwt.encode({
            'user_id': user["id"],
            'role': user.get("role", "普通用户"),
            'exp': datetime.datetime.now() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
        
        # 处理用户文档，使其可序列化
        user_dict = mongo_to_dict(user)
        
        # 删除密码字段
        user_dict.pop('password', None)
        
        # 返回用户信息
        user_info = user_dict
        
        return jsonify({
            "status": "success",
            "message": "登录成功",
            "data": {
                "user": user_info,
                "token": token
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"登录失败: {str(e)}"
        }), 500

# 获取当前用户信息
@auth_api.route('/api/me', methods=['GET'])
def get_current_user():
    try:
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
            
            # 从 MongoDB 中查找用户
            user = users_collection.find_one({"id": user_id})
            
            if not user:
                return jsonify({
                    "status": "error",
                    "message": "用户不存在"
                }), 404
            
            # 处理用户文档，使其可序列化
            user_dict = mongo_to_dict(user)
            
            # 删除密码字段
            user_dict.pop('password', None)
            
            # 返回用户信息
            user_info = user_dict
            
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
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"获取用户信息失败: {str(e)}"
        }), 500

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
