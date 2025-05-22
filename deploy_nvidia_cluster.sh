#!/bin/bash
# 部署NVIDIA集群的脚本

# 检查是否提供了密码
if [ -z "$1" ]; then
  echo "请提供SSH密码作为参数"
  echo "用法: ./deploy_nvidia_cluster.sh <密码>"
  exit 1
fi

PASSWORD=$1

# 注册NVIDIA集群
echo "正在注册NVIDIA集群..."
RESPONSE=$(curl -s -X POST http://localhost:5001/api/clusters -H "Content-Type: application/json" -d "{
  \"name\": \"NVIDIA GPU集群\",
  \"adapter_type\": \"nvidia\",
  \"center_node_ip\": \"47.116.124.254\",
  \"center_node_port\": 22,
  \"username\": \"root\",
  \"password\": \"$PASSWORD\",
  \"center_controller_url\": \"http://localhost:5001\",
  \"description\": \"阿里云NVIDIA GPU服务器\"
}")

echo "服务器响应: $RESPONSE"

# 解析响应，获取集群ID
CLUSTER_ID=$(echo $RESPONSE | grep -o '"cluster_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$CLUSTER_ID" ]; then
  echo "集群ID: $CLUSTER_ID"
  echo "集群注册成功！"
  
  # 等待几秒钟，让集群控制器启动
  echo "等待集群控制器启动..."
  sleep 5
  
  # 查询集群状态
  echo "查询集群状态..."
  CLUSTER_STATUS=$(curl -s -X GET http://localhost:5001/api/clusters/$CLUSTER_ID)
  echo "集群状态: $CLUSTER_STATUS"
else
  echo "集群注册失败，请检查错误信息。"
fi
