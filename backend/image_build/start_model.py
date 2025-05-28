#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动脚本 - 用于在容器内加载和运行Transformers模型
支持Apple GPU加速
"""

import os
import sys
import json
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, TextIteratorStreamer

def parse_args():
    parser = argparse.ArgumentParser(description="启动Transformers模型")
    parser.add_argument("--model_name", type=str, default="gpt2", help="模型名称或路径")
    parser.add_argument("--device", type=str, default="mps", help="运行设备 (cpu, mps)")
    parser.add_argument("--port", type=int, default=8000, help="API服务端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="API服务主机")
    parser.add_argument("--model_path", type=str, default=None, help="模型路径，如果与--model_name不同")
    return parser.parse_args()

def check_mps_availability():
    """检查MPS (Metal Performance Shaders) 是否可用"""
    if torch.backends.mps.is_available():
        print("MPS (Apple GPU加速) 可用")
        return True
    else:
        print("MPS (Apple GPU加速) 不可用，将使用CPU")
        if torch.backends.mps.is_built():
            print("PyTorch已编译支持MPS，但当前环境不支持")
        else:
            print("PyTorch未编译支持MPS")
        return False

def load_model(model_name, device):
    """加载模型和分词器"""
    print(f"正在加载模型: {model_name} 到设备: {device}")
    
    # 判断是否是本地模型路径
    is_local_path = os.path.exists(model_name)
    if is_local_path:
        print(f"检测到本地模型路径: {model_name}")
        # 如果是容器内路径，直接使用
        if model_name.startswith('/app/models/'):
            model_path = model_name
        else:
            # 如果是主机路径，转换为容器内路径
            model_path = '/app/models/local_model'
            print(f"警告: 使用的是主机路径，请确保已经挂载到容器内的 /app/models/local_model 目录")
    else:
        model_path = model_name
    
    # 设置适当的设备
    if device == "mps" and check_mps_availability():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
        print("使用CPU运行模型")
    
    # 检测是否是中文模型
    is_chinese_model = any(keyword in model_path.lower() for keyword in [
        'chinese', 'baichuan', 'qwen', 'chatglm', 'llama3', 'yi', 'internlm', 
        'xverse', 'bloom', 'glm', 'moss', 'falcon', 'ziya', 'aquila'
    ])
    
    print(f"检测到{'中文' if is_chinese_model else '非中文'}模型")
    
    try:
        # 加载分词器
        print(f"正在加载分词器从: {model_path}")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,  # 允许使用远程代码，对于一些中文模型必要
            padding_side="left"  # 对于大多数生成任务，左侧填充更合适
        )
        
        # 确保分词器有正确的EOS和PAD token
        if tokenizer.pad_token is None and tokenizer.eos_token is not None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # 加载模型
        print(f"正在加载模型从: {model_path}")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device.type == "mps" else torch.float32,
            low_cpu_mem_usage=True,
            trust_remote_code=True  # 允许使用远程代码，对于一些中文模型必要
        )
        
        # 将模型移至设备
        model.to(device)
        print(f"模型已加载到设备: {device}")
        
        return model, tokenizer, device
    except Exception as e:
        print(f"加载模型时出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise e

def start_api_server(model, tokenizer, host, port):
    """启动简单的API服务器"""
    from flask import Flask, request, jsonify, Response, stream_with_context
    import time
    import json
    
    app = Flask(__name__)
    
    @app.route('/generate', methods=['POST'])
    def generate():
        try:
            data = request.json
            prompt = data.get('prompt', '')
            max_length = data.get('max_length', 512)
            temperature = data.get('temperature', 0.7)
            top_p = data.get('top_p', 0.9)
            top_k = data.get('top_k', 50)
            
            print(f"\n\n收到生成请求:\n提示词: {prompt[:100]}...\n参数: max_length={max_length}, temp={temperature}, top_p={top_p}")
            
            start_time = time.time()
            
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(
                **inputs, 
                max_length=max_length, 
                num_return_sequences=1,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True
            )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 如果响应与提示词开头相同，则去除提示词部分
            if response.startswith(prompt):
                response = response[len(prompt):]
                
            elapsed_time = time.time() - start_time
            print(f"\n生成完成，用时: {elapsed_time:.2f}秒\n响应: {response[:100]}...")
            
            return jsonify({
                "response": response,
                "elapsed_time": elapsed_time
            })
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"\n生成错误: {error_msg}")
            return jsonify({"error": str(e), "traceback": error_msg}), 500
    
    @app.route('/chat', methods=['POST'])
    def chat():
        try:
            data = request.json
            messages = data.get('messages', [])
            max_length = data.get('max_length', 1024)
            temperature = data.get('temperature', 0.7)
            top_p = data.get('top_p', 0.9)
            
            if not messages:
                return jsonify({"error": "消息列表不能为空"}), 400
            
            print(f"\n\n收到聊天请求:\n消息数量: {len(messages)}\n最后一条: {messages[-1].get('content', '')[:100]}...")
            
            start_time = time.time()
            
            # 将消息列表转换为模型可以理解的格式
            # 这里采用简单的拼接方式，实际中可能需要根据不同模型调整
            prompt = ""
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'system':
                    prompt += f"<system>\n{content}\n</system>\n"
                elif role == 'user':
                    prompt += f"<human>\n{content}\n</human>\n"
                elif role == 'assistant':
                    prompt += f"<assistant>\n{content}\n</assistant>\n"
            
            # 添加最后的助手角色提示
            prompt += "<assistant>\n"
            
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(
                **inputs, 
                max_length=max_length, 
                num_return_sequences=1,
                temperature=temperature,
                top_p=top_p,
                do_sample=True
            )
            
            full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 提取助手的回复部分
            if "<assistant>" in full_response:
                parts = full_response.split("<assistant>")
                if len(parts) > 1:
                    # 获取最后一个助手标记后的内容
                    assistant_response = parts[-1].strip()
                    # 如果有结束标记，去除它
                    if "</assistant>" in assistant_response:
                        assistant_response = assistant_response.split("</assistant>")[0].strip()
                else:
                    assistant_response = full_response
            else:
                # 如果没有助手标记，则尝试去除提示词部分
                if full_response.startswith(prompt):
                    assistant_response = full_response[len(prompt):].strip()
                else:
                    assistant_response = full_response
                
            elapsed_time = time.time() - start_time
            print(f"\n聊天完成，用时: {elapsed_time:.2f}秒\n响应: {assistant_response[:100]}...")
            
            return jsonify({
                "response": assistant_response,
                "elapsed_time": elapsed_time
            })
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"\n聊天错误: {error_msg}")
            return jsonify({"error": str(e), "traceback": error_msg}), 500
    
    @app.route('/generate/stream', methods=['POST'])
    def generate_stream():
        """流式文本生成API"""
        try:
            data = request.json
            prompt = data.get('prompt', '')
            max_length = data.get('max_length', 512)
            temperature = data.get('temperature', 0.7)
            top_p = data.get('top_p', 0.9)
            top_k = data.get('top_k', 50)
            
            print(f"\n\n收到流式生成请求:\n提示词: {prompt[:100]}...\n参数: max_length={max_length}, temp={temperature}, top_p={top_p}")
            
            # 准备输入
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            generated_text = prompt
            
            def generate_stream_response():
                nonlocal generated_text
                
                # 发送初始消息
                yield json.dumps({"text": prompt, "done": False}) + "\n"
                
                # 设置生成参数
                gen_kwargs = {
                    "max_length": max_length,
                    "do_sample": True,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "pad_token_id": tokenizer.eos_token_id
                }
                
                # 流式生成
                streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
                generation_kwargs = {**inputs, **gen_kwargs, "streamer": streamer}
                
                # 在后台线程中运行生成
                from threading import Thread
                thread = Thread(target=model.generate, kwargs=generation_kwargs)
                thread.start()
                
                # 流式返回生成的文本
                for new_text in streamer:
                    generated_text += new_text
                    yield json.dumps({"text": new_text, "done": False}) + "\n"
                
                # 发送完成消息
                yield json.dumps({"text": "", "done": True}) + "\n"
            
            return Response(stream_with_context(generate_stream_response()), 
                           content_type='application/x-ndjson')
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"\n流式生成错误: {error_msg}")
            return jsonify({"error": str(e), "traceback": error_msg}), 500
    
    @app.route('/chat/stream', methods=['POST'])
    def chat_stream():
        """流式聊天API"""
        try:
            data = request.json
            messages = data.get('messages', [])
            max_length = data.get('max_length', 1024)
            temperature = data.get('temperature', 0.7)
            top_p = data.get('top_p', 0.9)
            
            if not messages:
                return jsonify({"error": "消息列表不能为空"}), 400
            
            print(f"\n\n收到流式聊天请求:\n消息数量: {len(messages)}\n最后一条: {messages[-1].get('content', '')[:100]}...")
            
            # 将消息列表转换为模型可以理解的格式
            prompt = ""
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'system':
                    prompt += f"<system>\n{content}\n</system>\n"
                elif role == 'user':
                    prompt += f"<human>\n{content}\n</human>\n"
                elif role == 'assistant':
                    prompt += f"<assistant>\n{content}\n</assistant>\n"
            
            # 添加最后的助手角色提示
            prompt += "<assistant>\n"
            
            # 准备输入
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            
            def generate_chat_stream():
                # 设置生成参数
                gen_kwargs = {
                    "max_length": max_length,
                    "do_sample": True,
                    "temperature": temperature,
                    "top_p": top_p,
                    "pad_token_id": tokenizer.eos_token_id
                }
                
                # 流式生成
                streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
                generation_kwargs = {**inputs, **gen_kwargs, "streamer": streamer}
                
                # 在后台线程中运行生成
                from threading import Thread
                thread = Thread(target=model.generate, kwargs=generation_kwargs)
                thread.start()
                
                # 流式返回生成的文本
                for new_text in streamer:
                    yield json.dumps({"text": new_text, "done": False}) + "\n"
                
                # 发送完成消息
                yield json.dumps({"text": "", "done": True}) + "\n"
            
            return Response(stream_with_context(generate_chat_stream()), 
                           content_type='application/x-ndjson')
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"\n流式聊天错误: {error_msg}")
            return jsonify({"error": str(e), "traceback": error_msg}), 500
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            "status": "healthy",
            "model": getattr(model, "name_or_path", "unknown"),
            "device": str(model.device)
        })
    
    print(f"API服务器启动在 http://{host}:{port}")
    print(f"提供的端点:\n- /generate: 文本生成\n- /generate/stream: 流式文本生成\n- /chat: 聊天对话\n- /chat/stream: 流式聊天对话\n- /health: 健康检查")
    app.run(host=host, port=port)

def main():
    """主函数"""
    args = parse_args()
    
    # 如果提供了model_path，使用model_path，否则使用model_name
    model_path = args.model_path if args.model_path is not None else args.model_name
    
    # 打印系统信息
    print("\n===== 系统信息 =====")
    print(f"Python版本: {sys.version}")
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA是否可用: {torch.cuda.is_available()}")
    print(f"MPS是否可用: {torch.backends.mps.is_available()}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 加载模型
    model, tokenizer, device = load_model(model_path, args.device)
    
    # 打印模型信息
    print("\n===== 模型信息 =====")
    print(f"模型路径: {model_path}")
    print(f"运行设备: {device}")
    
    # 启动API服务器
    start_api_server(model, tokenizer, args.host, args.port)

if __name__ == "__main__":
    main()
