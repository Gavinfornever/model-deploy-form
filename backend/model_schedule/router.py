import json
import random
import requests
from flask import Blueprint, request, Response, jsonify, current_app
from functools import wraps

# 创建Blueprint
router_bp = Blueprint('model_router', __name__)

# 从app.py导入model_instances
def get_model_instances():
    """获取当前可用的模型实例列表"""
    # 直接调用Docker API获取最新的模型实例信息
    try:
        response = requests.get('http://localhost:5000/api/models/docker')
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and isinstance(data['data'], list):
                print(f"从 Docker API 获取到 {len(data['data'])} 个模型实例")
                return data['data']
            else:
                print("从 Docker API 获取模型实例失败：响应格式不正确")
    except Exception as e:
        print(f"从 Docker API 获取模型实例时发生错误: {str(e)}")
    
    # 如果无法从 Docker API 获取，则回退到使用全局变量
    from app import model_instances
    print(f"使用全局变量中的 {len(model_instances)} 个模型实例")
    return model_instances

# 调度算法接口
class ModelScheduler:
    """模型调度器，负责选择合适的模型实例处理请求"""
    
    @staticmethod
    def random_select(model_instances):
        """随机选择一个可用的模型实例"""
        available_instances = [m for m in model_instances if m.get('status') == 'running']
        if not available_instances:
            return None
        return random.choice(available_instances)
    
    @staticmethod
    def round_robin(model_instances):
        """轮询算法（预留）"""
        # TODO: 实现轮询算法
        return ModelScheduler.random_select(model_instances)
    
    @staticmethod
    def least_load(model_instances):
        """最小负载算法（预留）"""
        # TODO: 实现最小负载算法
        return ModelScheduler.random_select(model_instances)

# 路由处理函数
@router_bp.route('/remote/generate/stream', methods=['POST'])
def remote_generate_stream():
    """将请求路由到随机选择的模型实例"""
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '无效的请求数据'}), 400
    
    # 获取可用的模型实例
    model_instances = get_model_instances()
    if not model_instances:
        return jsonify({'status': 'error', 'message': '没有可用的模型实例'}), 503
    
    # 使用调度算法选择模型实例
    selected_model = ModelScheduler.random_select(model_instances)
    if not selected_model:
        return jsonify({'status': 'error', 'message': '没有可用的模型实例'}), 503
    
    # 构建目标URL
    port = selected_model.get('port')
    if not port:
        return jsonify({'status': 'error', 'message': '模型端口未知'}), 500
    
    target_url = f"http://localhost:{port}/chat/stream"
    print(f"路由请求到模型实例: {selected_model['id']}, URL: {target_url}")
    
    # 转换请求格式（如果需要）
    if 'prompt' in data and 'messages' not in data:
        # 如果请求中只有prompt而没有messages，转换为chat格式
        data = {
            "messages": [
                {"role": "user", "content": data["prompt"]}
            ],
            **{k: v for k, v in data.items() if k != "prompt"}
        }
    
    # 设置请求头
    headers = {
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }
    
    def generate():
        """生成流式响应"""
        try:
            # 发送SSE头部
            yield "data: {\"text\": \"正在连接模型...\"}\n\n"
            
            # 打印请求详情以便调试
            print(f"\n发送请求到: {target_url}")
            print(f"请求头: {headers}")
            print(f"请求数据: {data}\n")
            
            try:
                # 发送请求并获取响应
                response = requests.post(
                    target_url,
                    headers=headers,
                    json=data,
                    stream=True,
                    timeout=30
                )
                
                # 打印响应状态和头信息
                print(f"响应状态码: {response.status_code}")
                print(f"响应头: {response.headers}")
                
                # 检查响应状态
                if response.status_code != 200:
                    error_msg = f"模型API返回错误: {response.status_code}"
                    print(f"错误详情: {response.text if hasattr(response, 'text') else ''}")
                    yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
                    yield "data: [DONE]\n\n"
                    return
            except Exception as e:
                error_msg = f"连接模型API时发生错误: {str(e)}"
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

# 注册Blueprint的函数
def register_router(app):
    """注册路由Blueprint到Flask应用"""
    app.register_blueprint(router_bp)
    print("模型路由器已注册")
