import React, { useState, useEffect, useRef } from 'react';
import { 
  Layout, Card, Input, Button, Select, 
  List, Avatar, Typography, Divider, Spin, 
  message, Space, Tag, Tooltip 
} from 'antd';
import { 
  SendOutlined, 
  RobotOutlined, 
  UserOutlined, 
  ClearOutlined, 
  SyncOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';

const { Content } = Layout;
const { Option } = Select;
const { Text, Title, Paragraph } = Typography;

const ModelChat = () => {
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);
  
  // 获取可用模型列表
  const fetchModels = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:5000/api/models');
      const result = await response.json();
      
      if (result.status === 'success') {
        // 只获取状态为running的模型
        const runningModels = result.data.models.filter(model => model.status === 'running');
        setModels(runningModels);
        
        if (runningModels.length > 0) {
          setSelectedModel(runningModels[0].id);
        }
      }
    } catch (error) {
      console.error('获取模型列表失败:', error);
      message.error('获取模型列表失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 发送消息
  const sendMessage = async () => {
    if (!inputMessage.trim() || !selectedModel) return;
    
    // 添加用户消息到消息列表
    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setSending(true);
    
    try {
      // 开始流式响应
      setIsStreaming(true);
      setStreamingMessage('');
      
      // 关闭之前的EventSource连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      
      // 创建新的EventSource连接
      const url = `http://127.0.0.1:5000/api/chat/stream?model_id=${selectedModel}&message=${encodeURIComponent(inputMessage)}`;
      eventSourceRef.current = new EventSource(url);
      
      let fullResponse = '';
      
      eventSourceRef.current.onmessage = (event) => {
        // 获取事件数据
        const rawData = event.data;
        
        // 如果是[DONE]标记，表示生成结束
        if (rawData === '[DONE]') {
          finishStreamingResponse(fullResponse);
          return;
        }
        
        try {
          // 尝试解析JSON
          const data = JSON.parse(rawData);
          
          if (data.text && typeof data.text === 'string') {
            // 如果收到的是包含多个data:消息的字符串
            if (data.text.includes('data:')) {
              // 分割成单独的消息
              const messages = data.text.split('\u0000');
              
              for (const msg of messages) {
                if (msg.trim() === '') continue;
                
                if (msg === 'data: [DONE]') {
                  finishStreamingResponse(fullResponse);
                  return;
                }
                
                if (msg.startsWith('data:')) {
                  try {
                    // 提取data:后面的JSON内容
                    const jsonStr = msg.substring(5).trim();
                    const msgData = JSON.parse(jsonStr);
                    
                    if (msgData.text) {
                      // 将文本添加到流式消息中
                      setStreamingMessage(prev => prev + msgData.text);
                      fullResponse += msgData.text;
                      
                      // 如果有finish_reason字段且不为null，表示生成结束
                      if (msgData.finish_reason) {
                        finishStreamingResponse(fullResponse);
                        return;
                      }
                    }
                  } catch (e) {
                    // JSON解析错误，忽略该消息
                    console.warn('JSON解析错误:', e, msg);
                  }
                }
              }
            } else {
              // 处理普通的text字段
              setStreamingMessage(prev => prev + data.text);
              fullResponse += data.text;
              
              // 如果有finish_reason字段且不为null，表示生成结束
              if (data.finish_reason) {
                finishStreamingResponse(fullResponse);
              }
            }
          } else if (data.error) {
            // 处理错误
            console.error('模型响应错误:', data.error);
            message.error(`模型响应错误: ${data.error}`);
            finishStreamingResponse(fullResponse || '模型响应出错');
          } else if (data.type === 'content') {
            // 兼容旧格式
            setStreamingMessage(prev => prev + data.content);
            fullResponse += data.content;
          } else if (data.type === 'done') {
            // 兼容旧格式
            finishStreamingResponse(data.full_content || fullResponse);
          }
        } catch (e) {
          // 如果不是JSON，处理原始数据
          
          // 处理data:{...}格式的响应
          if (rawData.startsWith('data:')) {
            try {
              // 提取data:后面的JSON内容
              const jsonStr = rawData.substring(5).trim();
              
              // 如果是[DONE]标记，表示生成结束
              if (jsonStr === '[DONE]') {
                finishStreamingResponse(fullResponse);
                return;
              }
              
              // 解析JSON
              const data = JSON.parse(jsonStr);
              
              if (data.text) {
                // 处理text字段
                const textContent = data.text;
                
                // 将文本添加到流式消息中
                setStreamingMessage(prev => prev + textContent);
                fullResponse += textContent;
              }
            } catch (innerError) {
              // JSON解析错误，可能是不完整的响应
              console.warn('JSON解析错误:', innerError, rawData);
            }
          } else {
            // 处理纯文本响应
            if (rawData.trim()) {
              setStreamingMessage(prev => prev + rawData);
              fullResponse += rawData;
            }
          }
        }
      };
      
      eventSourceRef.current.onerror = (error) => {
        console.error('流式响应错误:', error);
        message.error('获取模型响应失败');
        finishStreamingResponse(fullResponse || '连接中断');
      };
      
      // 辅助函数：完成流式响应
      const finishStreamingResponse = (content) => {
        setIsStreaming(false);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }
        
        // 添加完整的助手回复到消息列表
        const assistantMessage = {
          role: 'assistant',
          content: content,
          timestamp: new Date().toISOString()
        };
        
        // 清理流式消息并添加完整消息到列表
        setMessages(prev => [...prev, assistantMessage]);
        setStreamingMessage('');
        setSending(false);
      };
      
    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送消息失败');
      setIsStreaming(false);
      setSending(false);
    }
  };
  
  // 清空对话
  const clearConversation = () => {
    setMessages([]);
    setStreamingMessage('');
    setIsStreaming(false);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    message.success('对话已清空');
  };
  
  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    fetchModels();
    
    // 组件卸载时关闭EventSource连接
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);
  
  return (
    <Content style={{ padding: '20px' }}>
      <Card 
        title={
          <Space>
            <RobotOutlined />
            <span>模型对话</span>
          </Space>
        }
        extra={
          <Space>
            <Select
              style={{ width: 200 }}
              placeholder="选择模型"
              value={selectedModel}
              onChange={setSelectedModel}
              loading={loading}
              disabled={isStreaming || sending}
            >
              {models.map(model => (
                <Option key={model.id} value={model.id}>
                  {model.modelName} ({model.server}:{model.port})
                </Option>
              ))}
            </Select>
            <Tooltip title="清空对话">
              <Button 
                icon={<ClearOutlined />} 
                onClick={clearConversation}
                disabled={messages.length === 0 && !streamingMessage}
              />
            </Tooltip>
            <Tooltip title="刷新模型列表">
              <Button 
                icon={<SyncOutlined />} 
                onClick={fetchModels}
                loading={loading}
              />
            </Tooltip>
          </Space>
        }
        style={{ marginBottom: 20 }}
      >
        <div style={{ height: 'calc(100vh - 280px)', overflowY: 'auto', padding: '10px' }}>
          {messages.length === 0 && !streamingMessage ? (
            <div style={{ textAlign: 'center', color: '#999', marginTop: '100px' }}>
              <InfoCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <p>选择一个模型并开始对话</p>
            </div>
          ) : (
            <List
              itemLayout="horizontal"
              dataSource={messages}
              renderItem={message => (
                <List.Item style={{ padding: '10px 0' }}>
                  <List.Item.Meta
                    avatar={
                      message.role === 'user' ? (
                        <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
                      ) : (
                        <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
                      )
                    }
                    title={
                      <Space>
                        <Text strong>{message.role === 'user' ? '用户' : '助手'}</Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {new Date(message.timestamp).toLocaleString()}
                        </Text>
                      </Space>
                    }
                    description={
                      <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {message.content}
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          )}
          
          {/* 流式响应显示 */}
          {streamingMessage && (
            <>
              <List.Item style={{ padding: '10px 0' }}>
                <List.Item.Meta
                  avatar={
                    <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
                  }
                  title={
                    <Space>
                      <Text strong>助手</Text>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {new Date().toLocaleString()}
                      </Text>
                      {isStreaming && <Tag color="processing">生成中...</Tag>}
                    </Space>
                  }
                  description={
                    <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxWidth: '100%', overflow: 'hidden' }}>
                      {streamingMessage}
                      {isStreaming && <span className="cursor-blink">|</span>}
                    </div>
                  }
                />
              </List.Item>
            </>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        <Divider style={{ margin: '12px 0' }} />
        
        <div style={{ display: 'flex', marginTop: '10px' }}>
          <Input.TextArea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="输入您的问题..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            disabled={isStreaming || sending || !selectedModel}
            style={{ flex: 1, marginRight: '10px' }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={sendMessage}
            loading={sending}
            disabled={!inputMessage.trim() || isStreaming || !selectedModel}
          >
            发送
          </Button>
        </div>
      </Card>
    </Content>
  );
};

export default ModelChat;
