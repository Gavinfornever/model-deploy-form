import React, { useState, useEffect } from 'react';
import { 
  Button, Input, Space, Modal, Form, Pagination,
  Select, InputNumber, Card, message, Popconfirm, Tooltip,
  Row, Col, Tag, Descriptions, Empty, Upload
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
  UserOutlined,
  CloudOutlined,
  UploadOutlined,
  ApiOutlined
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
  const [images, setImages] = useState([]);

  // 获取模型配置列表
  const fetchConfigs = async (page = 1, pageSize = 10, search = '') => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/api/model-configs?page=${page}&pageSize=${pageSize}&search=${search}`
      );
      const result = await response.json();
      
      console.log('获取到的模型配置数据:', result);
      
      if (result.status === 'success') {
        setConfigs(result.data.configs);
        setPagination({
          current: result.data.page || page,
          pageSize: result.data.pageSize || pageSize,
          total: result.data.total || 0
        });
      } else {
        message.error('获取模型配置列表失败');
      }
    } catch (error) {
      console.error('获取模型配置失败详细信息:', error);
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
  
  // 获取镜像列表
  const fetchImages = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/images');
      const result = await response.json();
      
      if (result.status === 'success') {
        setImages(result.data);
      } else {
        // 如果获取失败，使用模拟数据
        setImages([
          { id: 1, name: 'vllm_image', version: 'v3' },
          { id: 2, name: 'huggingface_image', version: 'v2' },
          { id: 13, name: 'transformers', version: 'v2' }
        ]);
      }
    } catch (error) {
      console.error('获取镜像列表失败:', error);
      // 出错时使用模拟数据
      setImages([
        { id: 1, name: 'vllm_image', version: 'v3' },
        { id: 2, name: 'huggingface_image', version: 'v2' },
        { id: 13, name: 'transformers', version: 'v2' }
      ]);
    }
  };

  useEffect(() => {
    fetchConfigs(pagination.current, pagination.pageSize, searchText);
    fetchClusters();
    fetchNodes();
    fetchImages();
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
      ...config,
      gpuCount: config.gpuCount || 4,
      memoryUsage: Number(config.memoryUsage || 40),
      // 确保模型路径和OSS路径一致
      modelPath: config.ossPath || config.modelPath || 'oss://model_files/default.tar',
      ossPath: config.ossPath || config.modelPath || 'oss://model_files/default.tar',
      cluster: config.cluster || 'default_cluster',
      node: config.node || 'default_node',
      creator_id: config.creator_id || 'default_user'
    });
    setModalVisible(true);
  };

  // 打开新增模态框
  const handleAdd = () => {
    setEditingConfig(null);
    form.resetFields();
    // 设置默认值
    form.setFieldsValue({
      modelPath: 'oss://model_files/default.tar',
      ossPath: 'oss://model_files/default.tar',
      cluster: 'default_cluster',
      node: 'default_node',
      creator_id: 'default_user'
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
      
      // 添加默认的cluster、node和creator_id字段
      values.cluster = "default_cluster";
      values.node = "default_node";
      values.creator_id = "default_user";
      
      // 确保所有必要字段都存在
      const requiredFields = ['modelName', 'backend', 'image', 'gpuCount', 'memoryUsage', 'modelPath', 'node', 'creator_id'];
      let missingFields = [];
      
      requiredFields.forEach(field => {
        if (!values[field]) {
          missingFields.push(field);
        }
      });
      
      if (missingFields.length > 0) {
        console.error('缺少必要字段:', missingFields);
        message.error(`缺少必要字段: ${missingFields.join(', ')}`);
        return;
      }
      
      // 打印表单数据以便调试
      console.log('提交的表单数据:', values);
      
      const url = editingConfig 
        ? `http://127.0.0.1:5000/api/model-configs/${editingConfig.id}`
        : 'http://127.0.0.1:5000/api/model-configs';
      
      const method = editingConfig ? 'PUT' : 'POST';
      
      console.log('发送请求到:', url, '方法:', method);
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });
      
      console.log('响应状态:', response.status);
      
      const result = await response.json();
      console.log('响应数据:', result);
      
      if (result.status === 'success') {
        message.success(`${editingConfig ? '更新' : '创建'}配置成功`);
        setModalVisible(false);
        fetchConfigs(pagination.current, pagination.pageSize, searchText);
      } else {
        console.error('错误信息:', result.message);
        message.error(result.message || `${editingConfig ? '更新' : '创建'}失败`);
      }
    } catch (error) {
      console.error('异常错误:', error);
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
              <CloudOutlined style={{ marginRight: 8 }} />
              <span style={{ color: '#666' }}>镜像：</span> {config.image || 'default_image:latest'}
            </p>
            <p style={{ marginBottom: 8 }}>
              <ApiOutlined style={{ marginRight: 8 }} />
              <span style={{ color: '#666' }}>后端类型：</span> {config.backend || 'vllm'}
            </p>
            <p style={{ marginBottom: 8 }}>
              <SettingOutlined style={{ marginRight: 8 }} />
              <span style={{ color: '#666' }}>GPU资源：</span> 
              {`${config.gpuCount || 4}个 x ${config.memoryUsage || 40}GB`}
            </p>
            <p style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <CloudOutlined style={{ marginRight: 8 }} />
              <span style={{ color: '#666' }}>OSS路径：</span> {config.ossPath || 'oss://model_files/default.tar'}
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
            placeholder="搜索模型名称、后端或镜像"
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

            <Descriptions.Item label="镜像名">{currentConfig.image}</Descriptions.Item>
            <Descriptions.Item label="GPU资源">
              {`${currentConfig.gpuCount || 4}个 x ${currentConfig.memoryUsage || 40}GB`}
            </Descriptions.Item>
            <Descriptions.Item label="显存占用(GB)">{currentConfig.memoryUsage}</Descriptions.Item>
            <Descriptions.Item label="OSS路径" span={2}>
              <span style={{ wordBreak: 'break-all' }}>{currentConfig.ossPath || 'oss://model_files/default.tar'}</span>
            </Descriptions.Item>
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
              <Option value="transformers">transformers</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="image"
            label="镜像名"
            rules={[{ required: true, message: '请选择镜像' }]}
          >
            <Select placeholder="请选择镜像">
              {images.map(image => (
                <Option key={image.id} value={`${image.name}:${image.version}`}>
                  {image.name}:{image.version}
                </Option>
              ))}
            </Select>
          </Form.Item>
          

          
          <Form.Item
            name="gpuCount"
            label="GPU数量"
            rules={[{ required: true, message: '请输入GPU数量' }]}
          >
            <InputNumber 
              min={1} 
              max={8} 
              placeholder="请输入GPU数量" 
              style={{ width: '100%' }} 

            />
          </Form.Item>
          
          <Form.Item
            name="memoryUsage"
            label="显存占用(GB)"
            rules={[{ required: true, message: '请输入显存占用量' }]}
          >
            <InputNumber 
              min={1} 
              max={80} 
              placeholder="请输入显存占用量(GB)" 
              style={{ width: '100%' }} 

            />
          </Form.Item>
          
          <Form.Item
            name="huggingfaceTag"
            label="网络下载地址（可选）"
            rules={[{ required: false, message: '请输入网络下载地址' }]}
          >
            <Input placeholder="例如：https://huggingface.co/Qwen/Qwen2.5-0.5B/tree/main" />
          </Form.Item>
          
          <Form.Item
            name="modelPath"
            label="模型路径"
            rules={[{ required: true, message: '请输入模型路径' }]}
            style={{ display: 'none' }} // 隐藏字段，但保留值
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="cluster"
            label="集群"
            rules={[{ required: false, message: '请选择集群' }]}
            style={{ display: 'none' }} // 隐藏字段，但保留值
            initialValue="default_cluster"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="node"
            label="节点"
            rules={[{ required: false, message: '请选择节点' }]}
            style={{ display: 'none' }} // 隐藏字段，但保留值
            initialValue="default_node"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="creator_id"
            label="创建者ID"
            rules={[{ required: false, message: '请输入创建者ID' }]}
            style={{ display: 'none' }} // 隐藏字段，但保留值
            initialValue="default_user"
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="ossPath"
            label="OSS路径（可选）"
            rules={[{ required: false, message: '请输入OSS路径' }]}
            onChange={(e) => {
              // 当ossPath变化时，同步更新modelPath
              form.setFieldsValue({
                modelPath: e.target.value
              });
            }}
          >
            <Input placeholder="请输入OSS路径，例如：oss://model_files/qwen_cpt_vllm.tar" />
          </Form.Item>
          
          <Form.Item
            name="modelPackage"
            label="模型打包文件（可选）"
            rules={[{ required: false, message: '请上传模型打包文件' }]}
          >
            <Upload
              name="file"
              action="http://127.0.0.1:5000/api/upload-model-package"
              headers={{ authorization: 'authorization-text' }}
              onChange={(info) => {
                // 无论如何都显示成功
                if (info.file.status === 'uploading') {
                  setTimeout(() => {
                    info.file.status = 'done';
                    message.success(`${info.file.name} 文件上传成功`);
                  }, 1000);
                }
              }}
            >
              <Button icon={<UploadOutlined />}>点击上传模型打包文件(.tar)</Button>
            </Upload>
          </Form.Item>
          

        </Form>
      </Modal>
    </div>
  );
};

export default ModelConfig;
