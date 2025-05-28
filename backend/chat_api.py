from flask import Blueprint, request, Response, jsonify, stream_with_context
import json
import time
import random
import gradio as gr
import threading
import queue
import uuid
import requests

chat_api = Blueprint('chat_api', __name__)

# 模拟模型响应队列
response_queues = {}

# 模拟Gradio客户端连接到不同模型
model_clients = {}

class GradioModelClient:
    """与模型服务的连接"""
    def __init__(self, model_id, model_info):
        self.model_id = model_id
        self.model_info = model_info
        self.api_url = f"http://{model_info['server']}:{model_info['port']}/chat/stream"
        # self.api_url = f"http://{model_info['server']}:{model_info['port']}/generate/stream"
        self.token = "20548cb5a329260ead027437cb22590e945504abd419e2e44ba312feda2ff29e"  # 实际应用中应该从配置或环境变量获取
    
    def generate_stream(self, message):
        """调用实际API生成流式响应"""
        headers = {
            'token': self.token,
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        
        payload = json.dumps({
            "messages": [
                {"role": "user", "content": message}
            ],
            # "prompt": message,
            "max_length": 40,  # 减少max_length加快生成速度
            "temperature": 0.7,
            "top_p": 0.9
        })
        
        try:
            # 发送请求并获取响应
            response = requests.post(self.api_url, headers=headers, data=payload, stream=True)
            response.raise_for_status()
            
            # 处理流式响应并转发给前端
            accumulated_text = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        line_text = line.decode('utf-8')
                        print(f"收到流式响应: {line_text}")
                        
                        # 解析JSON响应
                        data = json.loads(line_text)
                        
                        # 提取文本并累加
                        if 'text' in data:
                            # 直接使用模型返回的完整文本
                            # 这里不再累加，而是直接使用模型返回的完整文本
                            current_text = data.get('text', '')
                            
                            # 转换为前端期望的格式
                            sse_data = {"text": current_text}
                            if data.get('done', False):
                                sse_data["done"] = True
                            
                            # 发送给前端
                            yield f"data: {json.dumps(sse_data)}"
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {str(e)}, 原始数据: {line_text}")
                    except Exception as e:
                        print(f"处理流式响应行时发生错误: {str(e)}")
                    
        except Exception as e:
            yield f"调用模型API时出错: {str(e)}"

def get_model_client(model_id, models):
    """获取或创建模型客户端"""
    if model_id not in model_clients:
        # 查找模型信息
        model_info = next((m for m in models if m['id'] == model_id), None)
        if model_info:
            model_clients[model_id] = GradioModelClient(model_id, model_info)
    
    return model_clients.get(model_id)

@chat_api.route('/chat/stream', methods=['GET'])
def stream_chat():
    """流式聊天API"""
    model_id = request.args.get('model_id')
    message = request.args.get('message')
    
    if not model_id or not message:
        return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
    
    # 从app.py中导入模型列表
    from app import model_instances
    
    # 获取模型客户端
    client = get_model_client(model_id, model_instances)
    if not client:
        return jsonify({'status': 'error', 'message': '模型不存在或未运行'}), 404
        
    # 记录API调用
    print(f"模型对话请求: 模型ID={model_id}, 消息={message}")
    
    # 使用SSE直接流式返回原始响应
    def generate():
        try:
            # 直接将模型的原始响应传递给前端
            for chunk in client.generate_stream(message):
                # 如果是[DONE]标记，直接发送
                if chunk == '[DONE]':
                    yield f"data: [DONE]\n\n"
                else:
                    # 将每个文本块包装为JSON并发送
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            
            # 确保发送完成信号
            yield f"data: [DONE]\n\n"
                
        except Exception as e:
            # 发送错误信息
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*'
        }
    )

@chat_api.route('/chat/models', methods=['GET'])
def get_available_models():
    """获取可用于聊天的模型列表"""
    # 从app.py中导入模型列表
    from app import model_instances
    
    # 只返回状态为running的模型
    running_models = [model for model in model_instances if model['status'] == 'running']
    
    return jsonify({
        'status': 'success',
        'data': {
            'models': running_models
        }
    }), 200
