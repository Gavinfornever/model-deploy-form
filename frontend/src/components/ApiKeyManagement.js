import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Space, Select, message, Popconfirm, Tag, Tooltip, Card, Typography } from 'antd';
import { PlusOutlined, DeleteOutlined, ReloadOutlined, EyeOutlined, EyeInvisibleOutlined, CopyOutlined, KeyOutlined } from '@ant-design/icons';
import moment from 'moment';

const { Option } = Select;
const { Text, Paragraph } = Typography;

const ApiKeyManagement = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [visibleKeys, setVisibleKeys] = useState({});
  const [regenerateModalVisible, setRegenerateModalVisible] = useState(false);
  const [currentKey, setCurrentKey] = useState(null);
  const [newKeyInfo, setNewKeyInfo] = useState(null);

  // 获取API密钥列表
  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const response = await fetch('http://127.0.0.1:5000/api/api-keys', {
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        }
      });
      const result = await response.json();
      if (result.status === 'success') {
        setApiKeys(result.data);
      } else {
        message.error('获取API密钥列表失败');
      }
    } catch (error) {
      message.error('获取API密钥列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  // 创建新API密钥
  const handleCreateApiKey = async (values) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const response = await fetch('http://127.0.0.1:5000/api/api-keys', {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(values)
      });
      
      const result = await response.json();
      if (result.status === 'success') {
        message.success('API密钥创建成功');
        setModalVisible(false);
        form.resetFields();
        
        // 显示新创建的密钥信息
        setNewKeyInfo(result.data);
        setRegenerateModalVisible(true);
        
        // 刷新列表
        fetchApiKeys();
      } else {
        message.error('创建API密钥失败: ' + result.message);
      }
    } catch (error) {
      message.error('创建API密钥失败: ' + error.message);
    }
  };

  // 删除API密钥
  const handleDeleteApiKey = async (id) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const response = await fetch(`http://127.0.0.1:5000/api/api-keys/${id}`, {
        method: 'DELETE',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      if (result.status === 'success') {
        message.success('API密钥删除成功');
        fetchApiKeys();
      } else {
        message.error('删除API密钥失败: ' + result.message);
      }
    } catch (error) {
      message.error('删除API密钥失败: ' + error.message);
    }
  };

  // 重新生成API密钥
  const handleRegenerateApiKey = async (id) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const response = await fetch(`http://127.0.0.1:5000/api/api-keys/${id}/regenerate`, {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      if (result.status === 'success') {
        message.success('API密钥重新生成成功');
        
        // 显示新生成的密钥信息
        setNewKeyInfo(result.data);
        setRegenerateModalVisible(true);
        
        // 刷新列表
        fetchApiKeys();
      } else {
        message.error('重新生成API密钥失败: ' + result.message);
      }
    } catch (error) {
      message.error('重新生成API密钥失败: ' + error.message);
    }
  };

  // 复制API密钥到剪贴板
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(
      () => {
        message.success('已复制到剪贴板');
      },
      (err) => {
        message.error('复制失败: ' + err);
      }
    );
  };

  // 切换API密钥可见性
  const toggleKeyVisibility = (id) => {
    setVisibleKeys(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // 表格列定义
  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '密钥',
      dataIndex: 'key',
      key: 'key',
      width: 300,
      render: (key, record) => (
        <Space>
          <Text style={{ fontFamily: 'monospace' }}>
            {visibleKeys[record.id] ? key : '••••••••••••••••••••••••••••••••'}
          </Text>
          <Button 
            icon={visibleKeys[record.id] ? <EyeInvisibleOutlined /> : <EyeOutlined />} 
            size="small" 
            type="text" 
            onClick={() => toggleKeyVisibility(record.id)}
          />
          <Button 
            icon={<CopyOutlined />} 
            size="small" 
            type="text" 
            onClick={() => copyToClipboard(key)}
          />
        </Space>
      ),
    },
    {
      title: '权限',
      dataIndex: 'scope',
      key: 'scope',
      width: 120,
      render: (scope) => {
        let color = 'blue';
        if (scope === '完全访问') color = 'red';
        else if (scope === '只读') color = 'green';
        return <Tag color={color}>{scope}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => moment(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '最后使用',
      dataIndex: 'last_used',
      key: 'last_used',
      width: 180,
      render: (date) => date ? moment(date).format('YYYY-MM-DD HH:mm:ss') : '/',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="重新生成密钥">
            <Button 
              type="link" 
              icon={<ReloadOutlined />} 
              onClick={() => {
                setCurrentKey(record);
                handleRegenerateApiKey(record.id);
              }}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除此API密钥吗?"
            onConfirm={() => handleDeleteApiKey(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="api-key-management">
      <Card 
        title={
          <Space>
            <KeyOutlined />
            <span>API密钥管理</span>
          </Space>
        }
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => setModalVisible(true)}
          >
            创建API密钥
          </Button>
        }
      >
        <Table 
          dataSource={apiKeys} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* 创建API密钥的表单 */}
      <Modal
        title="创建API密钥"
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateApiKey}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入API密钥名称' }]}
          >
            <Input placeholder="例如: 生产环境API密钥" />
          </Form.Item>
          
          <Form.Item
            name="scope"
            label="权限范围"
            rules={[{ required: true, message: '请选择权限范围' }]}
            initialValue="只读"
          >
            <Select>
              <Option value="只读">只读</Option>
              <Option value="读写">读写</Option>
              <Option value="完全访问">完全访问</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="expiration"
            label="有效期"
            initialValue="永不过期"
          >
            <Select>
              <Option value="30天">30天</Option>
              <Option value="90天">90天</Option>
              <Option value="365天">365天</Option>
              <Option value="永不过期">永不过期</Option>
            </Select>
          </Form.Item>
          
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit">创建</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 显示新生成的API密钥 */}
      <Modal
        title="API密钥信息"
        visible={regenerateModalVisible}
        onCancel={() => setRegenerateModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setRegenerateModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {newKeyInfo && (
          <div>
            <p>请保存您的API密钥，它只会显示一次！</p>
            <Card>
              <Paragraph>
                <Text strong>名称:</Text> {newKeyInfo.name}
              </Paragraph>
              <Paragraph>
                <Text strong>密钥:</Text> 
                <Text code copyable style={{ wordBreak: 'break-all' }}>
                  {newKeyInfo.key}
                </Text>
              </Paragraph>
              <Paragraph>
                <Text strong>权限范围:</Text> {newKeyInfo.scope}
              </Paragraph>
              <Paragraph>
                <Text strong>创建时间:</Text> {moment(newKeyInfo.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Paragraph>
              <Paragraph>
                <Text strong>过期时间:</Text> {newKeyInfo.expires_at ? moment(newKeyInfo.expires_at).format('YYYY-MM-DD HH:mm:ss') : '永不过期'}
              </Paragraph>
            </Card>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ApiKeyManagement;
