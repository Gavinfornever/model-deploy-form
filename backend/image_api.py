from flask import Blueprint, jsonify, request
import uuid
import os
import subprocess
import time
from datetime import datetime
from pymongo import MongoClient
import json
from werkzeug.utils import secure_filename
import oss2

image_api = Blueprint('image_api', __name__)

# OSS配置
OSS_ACCESS_KEY_ID = 'your_access_key_id'  # 替换为实际的OSS访问密钥ID
OSS_ACCESS_KEY_SECRET = 'your_access_key_secret'  # 替换为实际的OSS访问密钥密码
OSS_ENDPOINT = 'http://oss-cn-beijing.aliyuncs.com'  # 替换为实际的OSS终端节点
OSS_BUCKET_NAME = 'model-deploy-images'  # 替换为实际的OSS存储桶名称
OSS_BASE_URL = f'https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT.replace("http://", "")}'  # OSS基础URL

# 初始化OSS客户端
def get_oss_client():
    try:
        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        return bucket
    except Exception as e:
        print(f"初始化OSS客户端失败: {e}")
        return None

# 连接MongoDB
try:
    # 使用提供的用户名和密码连接MongoDB
    client = MongoClient('mongodb://root:650803@localhost:27017/')
    db = client['model_deploy_db']
    images_collection = db['images']
    
    # 只在集合为空时初始化数据
    if images_collection.count_documents({}) == 0:
        print("镜像集合为空，开始初始化数据")
        
        # 使用前端页面上的三个假镜像数据
        initial_images = [
            {
                "id": 1,
                "name": "vllm_image",
                "version": "v3",
                "size": "5.2GB",
                "createDate": "2025-04-15",
                "creator": "张三",
                "dockerfileContent": "FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 vllm==0.2.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000",
                "ossUrl": "oss://images/vllm/vllm_image_v3.tar"
            },
            {
                "id": 13,
                "name": "transformers",
                "version": "v2",
                "size": "4.8GB",
                "createDate": "2025-05-23",
                "creator": "王高",
                "dockerfileContent": "FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.1.0 transformers==4.36.0 accelerate==0.25.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000",
                "ossUrl": "oss://images/transformers/transformers_v2.tar"
            },
            {
                "id": 2,
                "name": "huggingface_image",
                "version": "v2",
                "size": "3.8GB",
                "createDate": "2025-04-10",
                "creator": "李四",
                "dockerfileContent": "FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 transformers==4.30.2 huggingface_hub==0.16.4\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 7860",
                "ossUrl": "oss://images/huggingface/huggingface_v2.tar"
            }
        ]
        images_collection.insert_many(initial_images)
        print("MongoDB初始化数据成功")
    
    print("MongoDB连接成功")
except Exception as e:
    print(f"MongoDB连接失败: {e}")
    # 如果连接失败，使用内存数据作为备用
    fallback_images = [
        {
            "id": 1,
            "name": "vllm_image",
            "version": "v3",
            "size": "5.2GB",
            "createDate": "2025-04-15",
            "creator": "张三",
            "dockerfileContent": "FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 vllm==0.2.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\n\nCMD [\"python3\", \"vllm_server.py\"]",
            "ossUrl": "https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/vllm_image/v3/vllm_image.tar"
        },
        {
            "id": 2,
            "name": "huggingface_image",
            "version": "v2",
            "size": "3.8GB",
            "createDate": "2025-04-10",
            "creator": "李四",
            "dockerfileContent": "FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 transformers==4.30.2 huggingface_hub==0.16.4\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 7860\n\nCMD [\"python3\", \"gradio_app.py\"]",
            "ossUrl": "https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/huggingface_image/v2/huggingface_image.tar"
        },
        {
            "id": 13,
            "name": "transformers",
            "version": "v2",
            "size": "4.8GB",
            "createDate": "2025-05-23",
            "creator": "王高",
            "dockerfileContent": "FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.1.0 transformers==4.36.0 accelerate==0.25.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\n\nCMD [\"python3\", \"api.py\"]",
            "ossUrl": "https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/transformers/v2/transformers.tar"
        }
    ]

@image_api.route('/images', methods=['GET'])
def get_images():
    try:
        images = list(images_collection.find({}, {'_id': 0}))
        return jsonify({
            'status': 'success',
            'data': images
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@image_api.route('/images/reset', methods=['POST'])
def reset_images():
    try:
        # 清空现有数据
        images_collection.delete_many({})
        
        # 使用前端页面上的三个假镜像数据
        initial_images = [
            {
                "id": 1,
                "name": "vllm_image",
                "version": "v3",
                "size": "5.2GB",
                "createDate": "2025-04-15",
                "creator": "张三",
                "dockerfileContent": "FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 vllm==0.2.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000",
                "ossUrl": "oss://images/vllm/vllm_image_v3.tar"
            },
            {
                "id": 13,
                "name": "transformers",
                "version": "v2",
                "size": "4.8GB",
                "createDate": "2025-05-23",
                "creator": "王高",
                "dockerfileContent": "FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.1.0 transformers==4.36.0 accelerate==0.25.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000",
                "ossUrl": "oss://images/transformers/transformers_v2.tar"
            },
            {
                "id": 2,
                "name": "huggingface_image",
                "version": "v2",
                "size": "3.8GB",
                "createDate": "2025-04-10",
                "creator": "李四",
                "dockerfileContent": "FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 transformers==4.30.2 huggingface_hub==0.16.4\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 7860",
                "ossUrl": "oss://images/huggingface/huggingface_v2.tar"
            }
        ]
        images_collection.insert_many(initial_images)
        
        return jsonify({
            'status': 'success',
            'message': '镜像集合已重置为前端页面上的三个假镜像数据'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@image_api.route('/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """获取单个镜像"""
    try:
        # 从 MongoDB 中获取指定镜像
        image = images_collection.find_one({'id': image_id}, {'_id': 0})
        if image:
            return jsonify({
                'status': 'success',
                'data': image
            })
        return jsonify({"status": "error", "message": "镜像不存在"}), 404
    except Exception as e:
        print(f"获取镜像失败: {e}")
        # 如果连接失败，使用备用数据
        image = next((img for img in fallback_images if img['id'] == image_id), None)
        if image:
            return jsonify({
                'status': 'success',
                'data': image
            })
        return jsonify({"status": "error", "message": "镜像不存在"}), 404

@image_api.route('/images', methods=['POST'])
def add_image():
    """添加新镜像"""
    data = request.json
    
    # 验证必要字段
    required_fields = ['name', 'version', 'size', 'createDate', 'creator', 'dockerfileContent']
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"缺少必要字段: {field}"}), 400
    
    try:
        # 生成新ID
        max_id_doc = images_collection.find_one(sort=[('id', -1)])
        new_id = max_id_doc['id'] + 1 if max_id_doc else 1
        
        # 创建新镜像
        new_image = {
            "id": new_id,
            "name": data['name'],
            "version": data['version'],
            "size": data['size'],
            "createDate": data['createDate'],
            "creator": data['creator'],
            "dockerfileContent": data['dockerfileContent'],
            "ossUrl": data.get('ossUrl', '')
        }
        
        # 添加到MongoDB
        images_collection.insert_one(new_image)
        
        # 移除MongoDB的_id字段后返回
        new_image.pop('_id', None)
        return jsonify({"status": "success", "data": new_image}), 201
    except Exception as e:
        print(f"添加镜像失败: {e}")
        # 如果连接失败，使用备用数据
        new_id = max(img['id'] for img in fallback_images) + 1 if fallback_images else 1
        
        new_image = {
            "id": new_id,
            "name": data['name'],
            "version": data['version'],
            "size": data['size'],
            "createDate": data['createDate'],
            "creator": data['creator'],
            "dockerfileContent": data.get('dockerfileContent', ''),
            "ossUrl": data.get('ossUrl', '')
        }
        
        fallback_images.append(new_image)
        return jsonify({"status": "success", "data": new_image}), 201

@image_api.route('/images/<int:image_id>', methods=['PUT'])
def update_image(image_id):
    """更新镜像"""
    data = request.json
    
    try:
        # 查找镜像
        image = images_collection.find_one({'id': image_id})
        if not image:
            return jsonify({"status": "error", "message": "镜像不存在"}), 404
        
        # 准备更新数据
        update_data = {}
        for key, value in data.items():
            if key != 'id':  # 不允许更新ID
                update_data[key] = value
        
        # 更新MongoDB中的镜像
        images_collection.update_one({'id': image_id}, {'$set': update_data})
        
        # 获取更新后的镜像
        updated_image = images_collection.find_one({'id': image_id}, {'_id': 0})
        return jsonify({"status": "success", "data": updated_image})
    except Exception as e:
        print(f"更新镜像失败: {e}")
        # 如果连接失败，使用备用数据
        image = next((img for img in fallback_images if img['id'] == image_id), None)
        if not image:
            return jsonify({"status": "error", "message": "镜像不存在"}), 404
        
        # 更新字段
        for key, value in data.items():
            if key != 'id':  # 不允许更新ID
                image[key] = value
        
        return jsonify({"status": "success", "data": image})

@image_api.route('/images/upload', methods=['POST'])
def upload_image():
    """上传镜像文件并添加镜像"""
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "没有文件上传"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "没有选择文件"}), 400
    
    # 获取表单数据
    name = request.form.get('name')
    version = request.form.get('version')
    size = request.form.get('size')
    createDate = request.form.get('createDate')
    creator = request.form.get('creator')
    dockerfileContent = request.form.get('dockerfileContent')
    
    # 验证必要字段
    required_fields = ['name', 'version', 'size', 'createDate', 'creator', 'dockerfileContent']
    for field in required_fields:
        if not locals()[field]:
            return jsonify({"status": "error", "message": f"缺少必要字段: {field}"}), 400
    
    try:
        # 上传文件到OSS
        bucket = get_oss_client()
        if not bucket:
            return jsonify({"status": "error", "message": "OSS客户端初始化失败"}), 500
        
        # 生成唯一的OSS对象名
        timestamp = int(time.time())
        filename = secure_filename(file.filename)
        oss_object_name = f"images/{name}/{version}/{timestamp}_{filename}"
        
        # 上传文件到OSS
        bucket.put_object(oss_object_name, file)
        
        # 生成OSS URL
        oss_url = f"{OSS_BASE_URL}/{oss_object_name}"
        
        # 生成新ID
        max_id_doc = images_collection.find_one(sort=[('id', -1)])
        new_id = max_id_doc['id'] + 1 if max_id_doc else 1
        
        # 创建新镜像记录
        new_image = {
            "id": new_id,
            "name": name,
            "version": version,
            "size": size,
            "createDate": createDate,
            "creator": creator,
            "dockerfileContent": dockerfileContent,
            "ossUrl": oss_url
        }
        
        # 添加到MongoDB
        images_collection.insert_one(new_image)
        
        # 移除MongoDB的_id字段后返回
        new_image.pop('_id', None)
        
        return jsonify({"status": "success", "data": new_image}), 201
    except Exception as e:
        print(f"上传镜像失败: {e}")
        return jsonify({"status": "error", "message": f"上传镜像失败: {str(e)}"}), 500

@image_api.route('/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """删除镜像"""
    try:
        # 查找镜像
        image = images_collection.find_one({'id': image_id})
        if not image:
            return jsonify({"status": "error", "message": "镜像不存在"}), 404
        
        # 从 MongoDB 中删除
        images_collection.delete_one({'id': image_id})
        
        return jsonify({"status": "success", "message": "镜像删除成功"})
    except Exception as e:
        print(f"删除镜像失败: {e}")
        # 如果连接失败，使用备用数据
        image = next((img for img in fallback_images if img['id'] == image_id), None)
        if not image:
            return jsonify({"status": "error", "message": "镜像不存在"}), 404
        
        # 从备用数据中删除
        fallback_images.remove(image)
        
        return jsonify({"status": "success", "message": "镜像删除成功"}), 200
