#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型部署API - 用于接收部署请求并启动模型
"""

import os
import sys
import json
import time
import subprocess
import threading
import logging
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建蓝图
model_deployment_api = Blueprint('model_deployment_api', __name__)

# 存储运行中的模型实例
running_models = {}

# 待添加到全局模型实例列表的模型
model_instances_to_add = []

def run_command(command, cwd=None):
    """运行shell命令并返回结果"""
    logger.info(f"执行命令: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return False, e.stderr

def deploy_model_thread(model_id, model_name, model_path, port, device, max_memory=None, image=None):
    """在后台线程中部署模型"""
    try:
        # 实际部署模型，调用run_qwen_mount.sh脚本
        logger.info(f"开始部署模型: {model_name} (模型 ID: {model_id})")
        logger.info(f"模型路径: {model_path}")
        logger.info(f"端口: {port}")
        logger.info(f"设备: {device}")
        logger.info(f"最大内存: {max_memory}G")
        logger.info(f"镜像: {image if image else 'transformers:apple-lite-v1'}")
        
        # 如果是OSS路径，使用本地测试模型路径
        if model_path.startswith('oss://'):
            logger.warning(f"检测到OSS路径: {model_path}，使用本地测试模型")
            model_path = "/Users/wanggao/CascadeProjects/model-deploy-form/models/Qwen2.5-0.5B"
        
        # 获取脚本目录
        script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_build")
        
        # 调用run_qwen_mount.sh脚本启动模型
        run_script_cmd = f"cd {script_dir} && ./run_qwen_mount.sh {port}"
        logger.info(f"执行命令: {run_script_cmd}")
        
        # 执行脚本
        success, output = run_command(run_script_cmd)
        
        if success:
            # 容器ID从输出中提取
            container_id = output.strip().split('\n')[4] if len(output.strip().split('\n')) > 4 else f"container-{model_id}"
            logger.info(f"模型 {model_id} 部署成功，容器ID: {container_id}")
            
            # 更新模型状态
            running_models[model_id]["status"] = "running"
            running_models[model_id]["container_id"] = container_id
            
            # 等待模型启动
            logger.info(f"等待模型启动 (10秒)...")
            time.sleep(10)
            
            # 检查模型是否正常运行
            health_check_cmd = f"curl -s http://localhost:{port}/health"
            health_success, health_output = run_command(health_check_cmd)
            
            if health_success and health_output.strip():
                logger.info(f"模型 {model_id} 健康检查通过: {health_output}")
                
                # 返回实际的API响应
                running_models[model_id]["api_response"] = {
                    "model": model_name,
                    "status": "loaded",
                    "device": device,
                    "max_memory": max_memory,
                    "port": port,
                    "api_url": f"http://localhost:{port}",
                    "endpoints": [
                        "/generate",
                        "/chat",
                        "/generate/stream",
                        "/chat/stream",
                        "/health"
                    ]
                }
            else:
                logger.warning(f"模型 {model_id} 健康检查失败，但容器已启动")
                running_models[model_id]["status"] = "warning"
                running_models[model_id]["warning"] = "健康检查失败，请稍后再试"
        else:
            logger.error(f"模型 {model_id} 部署失败: {output}")
            running_models[model_id]["status"] = "failed"
            running_models[model_id]["error"] = output
            return
        
        # 打印端口信息，方便测试
        logger.info(f"\n\n=== 模型部署成功 ===\n模型 ID: {model_id}\n模型名称: {model_name}\n端口: {port}\nAPI URL: http://localhost:{port}\n测试命令: curl http://localhost:{port}/health\n===\n")
        
        # 更新模型状态信息，使用全局变量而不是导入
        # 这样可以避免循环导入问题
        global model_instances_to_add
        
        # 创建一个新的模型实例
        new_model_instance = {
            "id": model_id,
            "modelId": model_id,
            "modelName": model_name,
            "backend": "mac",  # 使用mac作为后端标识
            "server": "localhost",
            "port": str(port),
            "gpu": "Apple Silicon",
            "status": "running",
            "cluster": "local",
            "modelPath": model_path,
            "node": "localhost",
            "creator_name": "当前用户"
        }
        
        # 将新模型添加到待添加列表
        if model_instances_to_add is None:
            model_instances_to_add = []
        model_instances_to_add.append(new_model_instance)
        
        # 直接将模型添加到全局模型实例列表中
        try:
            # 使用绝对导入避免循环导入问题
            import sys
            sys.path.append('/Users/wanggao/CascadeProjects/model-deploy-form/backend')
            from app import model_instances
            
            # 创建新的模型实例，保留用户提供的模型名称
            new_instance = {
                "id": model_id,
                "modelId": model_id,
                "modelName": model_name,  # 保留原始模型名称
                "backend": "mac",  # 使用mac作为后端标识
                "server": "localhost",
                "port": str(port),
                "gpu": "Apple Silicon",
                "status": "running",
                "cluster": "local",
                "modelPath": model_path,
                "node": "localhost",
                "creator_name": "当前用户"
            }
            
            # 检查模型是否已经在列表中
            model_exists = False
            for i, model in enumerate(model_instances):
                if model.get('id') == model_id:
                    model_exists = True
                    # 更新模型状态
                    model_instances[i] = new_instance
                    logger.info(f"更新模型 {model_id} 在全局模型实例列表中")
                    break
            
            # 如果模型不在列表中，添加它
            if not model_exists:
                model_instances.append(new_instance)
                logger.info(f"模型 {model_id} 已添加到全局模型实例列表，当前列表长度: {len(model_instances)}")
        except Exception as e:
            logger.warning(f"更新全局模型实例列表失败: {str(e)}")
        
        logger.info(f"模型 {model_id} 部署成功并已添加到模型列表")
    except Exception as e:
        logger.exception(f"部署模型 {model_id} 时发生异常: {str(e)}")
        running_models[model_id]["status"] = "failed"
        running_models[model_id]["error"] = str(e)

@model_deployment_api.route('/api/models/deploy', methods=['POST'])
def deploy_model():
    """部署模型API"""
    try:
        data = request.json
        
        # 验证必要参数
        required_fields = ['model_name', 'model_path']
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"缺少必要参数: {field}"}), 400
        
        # 获取参数
        model_name = data.get('model_name')
        model_path = data.get('model_path')
        device = data.get('device', 'cpu')  # 默认使用CPU
        port = data.get('port', 8000)
        max_memory = data.get('max_memory')  # 可选参数
        image = data.get('image')  # 镜像参数
        
        # 检查模型路径是否存在
        if not os.path.exists(model_path) and not model_path.startswith('oss://'):
            # 如果是OSS路径，使用本地测试模型路径
            logger.warning(f"模型路径不存在: {model_path}，使用本地测试模型")
            # 使用默认的测试模型路径
            model_path = "/Users/wanggao/models/qwen2.5-0.5b"
        
        # 检查端口是否被占用
        check_port_cmd = f"lsof -i :{port}"
        success, output = run_command(check_port_cmd)
        if success and output.strip():
            return jsonify({"status": "error", "message": f"端口 {port} 已被占用"}), 400
        
        # 生成唯一的模型ID
        model_id = f"{model_name.replace(' ', '_').lower()}_{int(time.time())}"
        
        # 记录模型信息
        model_info = {
            "id": model_id,
            "name": model_name,
            "path": model_path,
            "port": port,
            "device": device,
            "max_memory": max_memory,
            "image": image,
            "status": "deploying",
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_url": f"http://localhost:{port}"
        }
        
        running_models[model_id] = model_info
        
        # 在后台线程中部署模型
        thread = threading.Thread(
            target=deploy_model_thread,
            args=(model_id, model_name, model_path, port, device, max_memory, image)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "success",
            "message": "模型部署请求已接收，正在后台部署",
            "model_id": model_id,
            "model_info": model_info,
            "port": port,  # 添加端口信息
            "api_url": f"http://localhost:{port}"  # 添加API URL
        })
    
    except Exception as e:
        logger.exception(f"部署模型时发生异常: {str(e)}")
        return jsonify({"status": "error", "message": f"部署模型时发生异常: {str(e)}"}), 500

@model_deployment_api.route('/api/models/status/<model_id>', methods=['GET'])
def get_model_status(model_id):
    """获取模型状态API"""
    if model_id not in running_models:
        return jsonify({"status": "error", "message": f"模型 {model_id} 不存在"}), 404
    
    return jsonify({
        "status": "success",
        "model_info": running_models[model_id]
    })

@model_deployment_api.route('/api/models/list', methods=['GET'])
def list_models():
    """列出所有运行中的模型API"""
    return jsonify({
        "status": "success",
        "models": list(running_models.values())
    })

@model_deployment_api.route('/api/models/stop/<model_id>', methods=['POST'])
def stop_model(model_id):
    """停止模型API"""
    if model_id not in running_models:
        return jsonify({"status": "error", "message": f"模型 {model_id} 不存在"}), 404
    
    model_info = running_models[model_id]
    
    if "container_id" not in model_info:
        return jsonify({"status": "error", "message": f"模型 {model_id} 没有关联的容器ID"}), 400
    
    container_id = model_info["container_id"]
    
    # 停止Docker容器
    stop_cmd = f"docker stop {container_id}"
    success, output = run_command(stop_cmd)
    
    if success:
        model_info["status"] = "stopped"
        model_info["stop_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "status": "success",
            "message": f"模型 {model_id} 已停止",
            "model_info": model_info
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"停止模型 {model_id} 失败: {output}"
        }), 500

# 初始化函数
def init_model_deployment():
    """初始化模型部署模块"""
    # 检查Docker是否可用
    success, output = run_command("docker --version")
    if not success:
        logger.error("Docker未安装或无法运行，模型部署功能将不可用")
        return False
    
    logger.info(f"Docker版本: {output.strip()}")
    
    # 检查transformers:apple-lite-v1镜像是否存在
    success, output = run_command("docker images transformers:apple-lite-v1 --format '{{.Repository}}:{{.Tag}}'")
    if not success or not output.strip():
        logger.warning("transformers:apple-lite-v1镜像不存在，尝试构建...")
        
        # 构建镜像
        script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_build")
        build_cmd = f"cd {script_dir} && python build_transformers_apple_lite.py"
        
        success, output = run_command(build_cmd)
        if not success:
            logger.error(f"构建镜像失败: {output}")
            return False
        
        logger.info("镜像构建成功")
    
    logger.info("模型部署模块初始化完成")
    return True
