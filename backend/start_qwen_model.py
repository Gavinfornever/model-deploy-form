#!/usr/bin/env python3
"""
启动Qwen模型实例并注册到集群控制器
"""

import os
import sys
import time
import json
import uuid
import argparse
import requests
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

# 模拟Transformers模型
class QwenModel:
    def __init__(self, model_name="Qwen/Qwen-7B-Chat", gpu_id=None):
        self.model_name = model_name
        self.model_id = str(uuid.uuid4())
        self.backend_type = "transformers"
        self.endpoint = ""
        self.status = "initializing"
        self.gpu_id = gpu_id
        
        print(f"正在加载模型: {model_name}" + (f" 在GPU {gpu_id} 上" if gpu_id else ""))
        # 模拟模型加载时间
        time.sleep(2)
        print(f"模型 {model_name} 加载完成" + (f" 在GPU {gpu_id} 上" if gpu_id else ""))
        
    def generate(self, prompt, max_length=100):
        # 模拟模型推理
        print(f"收到推理请求: {prompt[:30]}...")
        # 模拟推理时间
        time.sleep(1)
        return f"这是来自 {self.model_name} 的回复: {prompt[:10]}..."

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 全局变量
model = None
model_info = {
    "model_id": "",
    "model_name": "",
    "model_type": "transformers",
    "endpoint": "",
    "status": "initializing",
    "gpu_id": None
}

@app.route('/api/generate', methods=['POST'])
def generate():
    """模型推理接口"""
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({"status": "error", "message": "缺少必要字段: prompt"}), 400
        
        prompt = data['prompt']
        max_length = data.get('max_length', 100)
        
        # 调用模型生成回复
        response = model.generate(prompt, max_length)
        
        return jsonify({
            "status": "success",
            "response": response,
            "model_id": model_info["model_id"],
            "model_name": model_info["model_name"]
        })
    except Exception as e:
        print(f"生成回复时出错: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "success",
        "message": "模型服务运行正常",
        "model_info": model_info,
        "timestamp": time.time()
    })

@app.route('/api/model_instances_info', methods=['GET'])
def model_instances_info():
    """获取模型实例信息接口，供集群控制器轮询"""
    return jsonify({
        "status": "success",
        "model_instances": [model_info],
        "timestamp": time.time()
    })

def register_with_cluster_controller(cluster_controller_url, model_data):
    """向集群控制器注册模型实例"""
    try:
        response = requests.post(
            f"{cluster_controller_url}/api/models",
            json=model_data,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"模型实例注册成功: {response.json()}")
            return True
        else:
            print(f"模型实例注册失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"注册模型实例时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='启动Qwen模型实例')
    parser.add_argument('--model-name', type=str, default="Qwen/Qwen-7B-Chat", help='模型名称')
    parser.add_argument('--port', type=int, default=5010, help='服务器端口')
    parser.add_argument('--cluster-controller', type=str, default="http://localhost:5010", help='集群控制器URL')
    parser.add_argument('--gpu-id', type=str, help='指定使用的GPU ID')
    parser.add_argument('--memory-required', type=int, default=0, help='所需GPU内存(MB)')
    args = parser.parse_args()
    
    global model, model_info
    
    # 初始化模型
    model = QwenModel(model_name=args.model_name, gpu_id=args.gpu_id)
    
    # 设置模型信息
    model_info["model_id"] = model.model_id
    model_info["model_name"] = model.model_name
    model_info["endpoint"] = f"http://localhost:{args.port}/api/generate"
    model_info["status"] = "online"
    model_info["gpu_id"] = args.gpu_id
    if args.memory_required > 0:
        model_info["memory_required"] = args.memory_required
    
    # 启动Flask服务器
    print(f"启动模型服务器在端口 {args.port}" + (f", 使用GPU {args.gpu_id}" if args.gpu_id else ""))
    
    # 注册到集群控制器
    register_thread = threading.Thread(
        target=register_with_cluster_controller,
        args=(args.cluster_controller, model_info)
    )
    register_thread.daemon = True
    register_thread.start()
    
    print(f"启动模型服务器，监听端口: {args.port}")
    app.run(host='0.0.0.0', port=args.port)

if __name__ == "__main__":
    main()
