#!/bin/bash

# 运行Qwen2.5-0.5B模型的脚本 - 使用挂载方式加载所有文件
# 使用方法: ./run_qwen_mount.sh [端口号]

# 默认端口
PORT=${1:-8000}

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 获取项目根目录
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 模型路径
MODEL_PATH="$PROJECT_ROOT/models/Qwen2.5-0.5B"

# 检查模型路径是否存在
if [ ! -d "$MODEL_PATH" ]; then
    echo "错误: 模型路径不存在: $MODEL_PATH"
    echo "请确保已经下载Qwen2.5-0.5B模型到 $MODEL_PATH 目录"
    exit 1
fi

echo "===== 启动Qwen2.5-0.5B模型 ====="
echo "模型路径: $MODEL_PATH"
echo "脚本路径: $SCRIPT_DIR"
echo "API端口: $PORT"
echo "使用设备: cpu (因为Docker容器内无法访问Apple GPU)"

# 运行Docker容器，使用挂载方式加载所有文件
# 使用 -d 参数使容器在后台运行
docker run --platform=linux/arm64 -d --rm \
  --privileged \
  --name qwen-model-$PORT \
  -v "$MODEL_PATH":/app/models/local_model \
  -v "$SCRIPT_DIR":/app/scripts \
  -p $PORT:8000 \
  transformers:apple-lite-v1 \
  python /app/scripts/start_model.py \
    --model_name /app/models/local_model \
    --device cpu \
    --port 8000 \
    --host 0.0.0.0

echo "容器已在后台启动，可以通过以下命令查看日志："
echo "docker logs -f qwen-model-$PORT"
echo "模型 API 地址： http://localhost:$PORT"
echo "可以使用以下命令测试模型："
echo "curl http://localhost:$PORT/health"
echo "curl -X POST http://localhost:$PORT/generate -H \"Content-Type: application/json\" -d '{\"prompt\": \"Hello, who are you?\", \"max_length\": 50, \"temperature\": 0.7, \"top_p\": 0.9}'"
echo "要停止容器，请运行： docker stop qwen-model-$PORT"
