import React, { useState, useEffect } from 'react';
import { 
  Button, Input, Space, Modal, Form, Pagination,
  Select, InputNumber, Card, message, Popconfirm, Tooltip,
  Row, Col, Tag, Descriptions, Empty
} from 'antd';
import { 
  SearchOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined,
  InfoCircleOutlined,
  EyeOutlined,
  SettingOutlined,
  CodeOutlined,
  ClusterOutlined,
  DesktopOutlined,
  UserOutlined
} from '@ant-design/icons';

const { Option } = Select;

const ModelConfig = () => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [searchText, setSearchText] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [editingConfig, setEditingConfig] = useState(null);
  const [clusters, setClusters] = useState([]);
  const [nodes, setNodes] = useState([]);

  // 获取模型配置列表
  const fetchConfigs = async (page = 1, pageSize = 10, search = '') => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/api/model-configs?page=${page}&pageSize=${pageSize}&search=${search}`
      );
      const result = await response.json();
      
      if (result.status === 'success') {
        setConfigs(result.data.configs);
        setPagination({
          current: result.data.pagination.current,
          pageSize: result.data.pagination.pageSize,
          total: result.data.pagination.total
        });
      } else {
        message.error('获取模型配置列表失败');
      }
    } catch (error) {
      message.error('获取模型配置列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 获取集群列表
  const fetchClusters = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/clusters');
      const result = await response.json();
      
      if (result.status === 'success') {
        setClusters(result.data);
      }
    } catch (error) {
      console.error('获取集群列表失败:', error);
    }
  };

  // 获取节点列表
  const fetchNodes = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/nodes');
      const result = await response.json();
      
      if (result.status === 'success') {
        setNodes(result.data);
      }
    } catch (error) {
      console.error('获取节点列表失败:', error);
    }
  };

  useEffect(() => {
    fetchConfigs(pagination.current, pagination.pageSize, searchText);
    fetchClusters();
    fetchNodes();
  }, []);

  // 处理表格变化（分页、筛选、排序）
  const handleTableChange = (pagination) => {
    fetchConfigs(pagination.current, pagination.pageSize, searchText);
  };

  // 处理搜索
  const handleSearch = () => {
    fetchConfigs(1, pagination.pageSize, searchText);
  };

  // 处理搜索框按键事件
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // 打开编辑模态框
  const handleEdit = (config) => {
    setEditingConfig(config);
    form.setFieldsValue({
      ...form.getFieldsValue(),
      gpuIds: form.getFieldValue('gpuIds') || [0],
      memoryUsage: Number(form.getFieldValue('memoryUsage'))
    });
    setModalVisible(true);
  };

  // 打开新增模态框
  const handleAdd = () => {
    setEditingConfig(null);
    form.resetFields();
    form.setFieldsValue({
      image: 'deploy_image:v3',
      creator_id: '1' // 默认创建者ID
    });
    setModalVisible(true);
  };

  // 删除配置
  const handleDelete = async (configId) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/model-configs/${configId}`, {
        method: 'DELETE',
      });
      const result = await response.json();
      
      if (result.status === 'success') {
        message.success('配置删除成功');
        fetchConfigs(pagination.current, pagination.pageSize, searchText);
      } else {
        message.error(result.message || '删除失败');
      }
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      const url = editingConfig 
        ? `http://127.0.0.1:5000/api/model-configs/${editingConfig.id}`
        : 'http://127.0.0.1:5000/api/model-configs';
      
      const method = editingConfig ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        message.success(`${editingConfig ? '更新' : '创建'}配置成功`);
        setModalVisible(false);
        fetchConfigs(pagination.current, pagination.pageSize, searchText);
      } else {
        message.error(result.message || `${editingConfig ? '更新' : '创建'}失败`);
      }
    } catch (error) {
      message.error(`${editingConfig ? '更新' : '创建'}失败: ` + error.message);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '主键',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '模型名称',
      dataIndex: 'modelName',
      key: 'modelName',
      width: 150,
      render: (text) => <span style={{ fontWeight: 'bold' }}>{text}</span>,
    },
    {
      title: '部署后端',
      dataIndex: 'backend',
      key: 'backend',
      width: 100,
    },
    {
      title: '模型路径',
      dataIndex: 'modelPath',
      key: 'modelPath',
      width: 200,
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <span>{text}</span>
        </Tooltip>
      ),
    },
    {
      title: '模型集群',
      dataIndex: 'cluster',
      key: 'cluster',
      width: 120,
    },
    {
      title: '镜像名',
      dataIndex: 'image',
      key: 'image',
      width: 120,
    },
    {
      title: '模型节点',
      dataIndex: 'node',
      key: 'node',
      width: 100,
    },
    {
      title: 'GPU数量',
      dataIndex: 'gpuCount',
      key: 'gpuCount',
      width: 90,
    },
    {
      title: '显存占用(GB)',
      dataIndex: 'memoryUsage',
      key: 'memoryUsage',
      width: 120,
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      key: 'createTime',
      width: 150,
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此配置吗?"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              danger 
              icon={<DeleteOutlined />}
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 卡片渲染函数
  // 跳转到部署页面
  const handleDeployModel = (config) => {
    // 使用 localStorage 临时存储选中的配置，以便在部署页面使用
    localStorage.setItem('selectedModelConfig', JSON.stringify(config));
    // 跳转到部署页面
    window.location.href = '/deploy';
  };

  const renderConfigCard = (config) => {
    return (
      <Col xs={24} sm={12} md={8} lg={6} key={config.id}>
        <Card
          hoverable
          style={{ marginBottom: 16 }}
          onClick={() => handleDeployModel(config)}
          actions={[
            <Tooltip title="部署此模型">
              <Button type="primary" size="small" onClick={(e) => {
                e.stopPropagation(); // 阻止事件冒泡
                handleDeployModel(config);
              }}>部署</Button>
            </Tooltip>,
            <Tooltip title="查看详情">
              <EyeOutlined key="view" onClick={(e) => {
                e.stopPropagation(); // 阻止事件冒泡
                handleViewDetails(config);
              }} />
            </Tooltip>,
            <Tooltip title="编辑">
              <EditOutlined key="edit" onClick={(e) => {
                e.stopPropagation(); // 阻止事件冒泡
                handleEdit(config);
              }} />
            </Tooltip>,
            <Popconfirm
              title="确定要删除此配置吗?"
              onConfirm={(e) => {
                e.stopPropagation(); // 阻止事件冒泡
                handleDelete(config.id);
              }}
              okText="确定"
              cancelText="取消"
              onCancel={(e) => e.stopPropagation()} // 阻止事件冒泡
            >
              <DeleteOutlined key="delete" onClick={(e) => e.stopPropagation()} />
            </Popconfirm>
          ]}
        >
          <div style={{ height: 180 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Tag color="blue">{config.backend}</Tag>
              <span style={{ fontSize: 12, color: '#999' }}>{config.id}</span>
            </div>
            <h3 style={{ marginBottom: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {config.modelName}
            </h3>
            <p style={{ marginBottom: 8 }}>
              <ClusterOutlined style={{ marginRight: 8 }} />
              <span style={{ color: '#666' }}>集群：</span> {config.cluster}
            </p>
            <p style={{ marginBottom: 8 }}>
              <DesktopOutlined style={{ marginRight: 8 }} />
              <span style={{ color: '#666' }}>节点：</span> {config.node}
            </p>
            <p style={{ marginBottom: 8 }}>
              <SettingOutlined style={{ marginRight: 8 }} />
              <span style={{ color: '#666' }}>指定GPU：</span> 
              {config.gpuIds ? config.gpuIds.map(id => `GPU-${id}`).join(', ') : 
               (config.gpuCount ? `${config.gpuCount}个` : 'GPU-0')} / {config.memoryUsage} GB
            </p>
            <p style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <CodeOutlined style={{ marginRight: 8 }} />
              <span style={{ color: '#666' }}>路径：</span> {config.modelPath}
            </p>
          </div>
        </Card>
      </Col>
    );
  };

  // 查看配置详情
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentConfig, setCurrentConfig] = useState(null);

  const handleViewDetails = (config) => {
    setCurrentConfig(config);
    setDetailVisible(true);
  };

  return (
    <div className="model-config-container">
      <Card title="模型配置管理" style={{ width: '100%' }}>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <Input.Search
            placeholder="搜索模型名称、后端、集群或节点"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onSearch={handleSearch}
            onPressEnter={handleKeyPress}
            style={{ width: 300 }}
          />
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={handleAdd}
          >
            添加配置
          </Button>
        </div>
        
        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <div className="ant-spin ant-spin-lg ant-spin-spinning">
              <span className="ant-spin-dot ant-spin-dot-spin">
                <i className="ant-spin-dot-item"></i>
                <i className="ant-spin-dot-item"></i>
                <i className="ant-spin-dot-item"></i>
                <i className="ant-spin-dot-item"></i>
              </span>
            </div>
          </div>
        ) : configs.length > 0 ? (
          <>
            <Row gutter={[16, 16]}>
              {configs.map(config => renderConfigCard(config))}
            </Row>
            <div style={{ textAlign: 'right', marginTop: 16 }}>
              <Pagination
                current={pagination.current}
                pageSize={pagination.pageSize}
                total={pagination.total}
                onChange={(page, pageSize) => fetchConfigs(page, pageSize, searchText)}
                showSizeChanger
                showTotal={(total) => `共 ${total} 条数据`}
              />
            </div>
          </>
        ) : (
          <Empty description="暂无模型配置" />
        )}
      </Card>

      {/* 模型配置详情模态框 */}
      <Modal
        title="模型配置详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="edit" type="primary" onClick={() => {
            setDetailVisible(false);
            handleEdit(currentConfig);
          }}>
            编辑
          </Button>,
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {currentConfig && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="主键" span={2}>{currentConfig.id}</Descriptions.Item>
            <Descriptions.Item label="模型名称" span={2}>{currentConfig.modelName}</Descriptions.Item>
            <Descriptions.Item label="部署后端">{currentConfig.backend}</Descriptions.Item>
            <Descriptions.Item label="模型集群">{currentConfig.cluster}</Descriptions.Item>
            <Descriptions.Item label="模型节点">{currentConfig.node}</Descriptions.Item>
            <Descriptions.Item label="镜像名">{currentConfig.image}</Descriptions.Item>
            <Descriptions.Item label="指定GPU">
              {currentConfig.gpuIds ? currentConfig.gpuIds.map(id => `GPU-${id}`).join(', ') : 
               (currentConfig.gpuCount ? `${currentConfig.gpuCount}个` : 'GPU-0')}
            </Descriptions.Item>
            <Descriptions.Item label="显存占用(GB)">{currentConfig.memoryUsage}</Descriptions.Item>
            <Descriptions.Item label="模型路径" span={2}>
              <span style={{ wordBreak: 'break-all' }}>{currentConfig.modelPath}</span>
            </Descriptions.Item>
            <Descriptions.Item label="创建者ID">{currentConfig.creator_id}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{currentConfig.createTime}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 配置表单模态框 */}
      <Modal
        title={editingConfig ? '编辑模型配置' : '添加模型配置'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText={editingConfig ? '更新' : '创建'}
        cancelText="取消"
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="modelName"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="请输入模型名称" />
          </Form.Item>
          
          <Form.Item
            name="backend"
            label="部署后端"
            rules={[{ required: true, message: '请选择部署后端' }]}
          >
            <Select placeholder="请选择部署后端">
              <Option value="vllm">vllm</Option>
              <Option value="general">general</Option>
              <Option value="vilm">vilm</Option>
              <Option value="yllm">yllm</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="modelPath"
            label="模型路径"
            rules={[{ required: true, message: '请输入模型路径' }]}
          >
            <Input placeholder="请输入模型路径" />
          </Form.Item>
          
          <Form.Item
            name="cluster"
            label="模型集群"
            rules={[{ required: true, message: '请选择模型集群' }]}
          >
            <Select placeholder="请选择模型集群">
              {clusters.map(cluster => (
                <Option key={cluster} value={cluster}>{cluster}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="image"
            label="镜像名"
            rules={[{ required: true, message: '请输入镜像名' }]}
          >
            <Input placeholder="请输入镜像名" />
          </Form.Item>
          
          <Form.Item
            name="node"
            label="模型节点"
            rules={[{ required: true, message: '请选择模型节点' }]}
          >
            <Select placeholder="请选择模型节点">
              {nodes.map(node => (
                <Option key={node} value={node}>{node}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="gpuIds"
            label="指定GPU"
            rules={[{ required: true, message: '请指定GPU序号' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择GPU序号"
              style={{ width: '100%' }}
            >
              {[0, 1, 2, 3, 4, 5, 6, 7].map(id => (
                <Option key={id} value={id}>GPU-{id}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="memoryUsage"
            label="显存占用(GB)"
            rules={[{ required: true, message: '请输入显存占用量' }]}
          >
            <InputNumber min={1} placeholder="请输入显存占用量(GB)" style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="creator_id"
            label="创建者ID"
            rules={[{ required: true, message: '请输入创建者ID' }]}
          >
            <Input placeholder="请输入创建者ID" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ModelConfig;
