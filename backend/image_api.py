from flask import Blueprint, jsonify, request
import uuid
from datetime import datetime

image_api = Blueprint('image_api', __name__)

# 模拟数据库
images = [
    {
        "id": 1,
        "name": "vllm_image",
        "version": "v3",
        "cluster": "集群A",
        "size": "5.2GB",
        "createDate": "2025-04-15",
        "creator": "张三"
    },
    {
        "id": 2,
        "name": "huggingface_image",
        "version": "v2",
        "cluster": "集群B",
        "size": "3.8GB",
        "createDate": "2025-04-10",
        "creator": "李四"
    }
]

@image_api.route('/images', methods=['GET'])
def get_images():
    """获取所有镜像"""
    return jsonify(images)

@image_api.route('/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """获取单个镜像"""
    image = next((img for img in images if img['id'] == image_id), None)
    if image:
        return jsonify(image)
    return jsonify({"error": "镜像不存在"}), 404

@image_api.route('/images', methods=['POST'])
def add_image():
    """添加新镜像"""
    data = request.json
    
    # 验证必要字段
    required_fields = ['name', 'version', 'cluster', 'size', 'createDate', 'creator']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"缺少必要字段: {field}"}), 400
    
    # 创建新镜像
    new_image = {
        "id": max(img['id'] for img in images) + 1 if images else 1,
        "name": data['name'],
        "version": data['version'],
        "cluster": data['cluster'],
        "size": data['size'],
        "createDate": data['createDate'],
        "creator": data['creator']
    }
    
    images.append(new_image)
    return jsonify(new_image), 201

@image_api.route('/images/<int:image_id>', methods=['PUT'])
def update_image(image_id):
    """更新镜像"""
    data = request.json
    
    # 查找要更新的镜像
    image_index = next((i for i, img in enumerate(images) if img['id'] == image_id), None)
    if image_index is None:
        return jsonify({"error": "镜像不存在"}), 404
    
    # 更新镜像
    for key, value in data.items():
        if key != 'id':  # 不允许更新ID
            images[image_index][key] = value
    
    return jsonify(images[image_index])

@image_api.route('/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """删除镜像"""
    global images
    initial_length = len(images)
    images = [img for img in images if img['id'] != image_id]
    
    if len(images) < initial_length:
        return jsonify({"message": "镜像已删除"}), 200
    return jsonify({"error": "镜像不存在"}), 404
