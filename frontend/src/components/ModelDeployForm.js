import React, { useState, useEffect } from 'react';
import { 
  Form, Input, Button, Select, InputNumber, message, 
  Card, Row, Col, Typography, Divider, Spin, Tooltip
} from 'antd';
import { 
  CloudOutlined, SettingOutlined, DeploymentUnitOutlined, 
  InfoCircleOutlined, SaveOutlined, ClearOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;
const { Title } = Typography;

const ModelDeployForm = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [modelConfigs, setModelConfigs] = useState([]);
  const [images, setImages] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);

  // 获取模型配置列表
  const fetchModelConfigs = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:5000/api/model-configs');
      const result = await response.json();
      
      if (result.status === 'success') {
        setModelConfigs(result.data.configs || []);
      } else {
        message.error(result.message || '获取模型配置失败');
      }
    } catch (error) {
      console.error('获取模型配置失败:', error);
      message.error('获取模型配置失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取镜像列表
  const fetchImages = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/images');
      const result = await response.json();
      setImages(result || []);
    } catch (error) {
      console.error('获取镜像列表失败:', error);
      // 使用模拟数据
      setImages([
        {
          id: 1,
          name: 'vllm_image',
          version: 'v3',
          cluster: 'muxi集群',
          size: '5.2GB',
          createDate: '2025-04-15',
          creator: '张三'
        },
        {
          id: 2,
          name: 'huggingface_image',
          version: 'v2',
          cluster: 'A10集群',
          size: '3.8GB',
          createDate: '2025-04-10',
          creator: '李四'
        },
        // 其他镜像...
      ]);
    }
  };

  // 获取集群列表
  const fetchClusters = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/clusters');
      const result = await response.json();
      setClusters(result.data || ['muxi集群', 'A10集群', 'A100集群']);
    } catch (error) {
      console.error('获取集群列表失败:', error);
      setClusters(['muxi集群', 'A10集群', 'A100集群']);
    }
  };

  // 获取节点列表
  const fetchNodes = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/nodes');
      const result = await response.json();
      setNodes(result.data || ['node1', 'node2', 'node3', 'node4']);
    } catch (error) {
      console.error('获取节点列表失败:', error);
      setNodes(['node1', 'node2', 'node3', 'node4']);
    }
  };

  // 初始化加载数据
  useEffect(() => {
    fetchModelConfigs();
    fetchImages();
    fetchClusters();
    fetchNodes();
    
    // 检查是否有从其他页面传递过来的数据
    const storedConfig = localStorage.getItem('selectedModelConfig');
    const storedImage = localStorage.getItem('selectedImage');
    
    if (storedConfig) {
      try {
        const config = JSON.parse(storedConfig);
        setSelectedConfig(config);
        
        // 将gpuCount转换为gpuIds数组
        const gpuIds = config.gpuIds || 
          (config.gpuCount ? Array.from({length: config.gpuCount}, (_, i) => i) : [0]);
          
        // 自动填充表单
        form.setFieldsValue({
          configId: config.id,
          modelName: config.modelName,
          backend: config.backend,
          modelPath: config.modelPath,
          cluster: config.cluster,
          node: config.node,
          gpuIds: gpuIds,
          memoryUsage: config.memoryUsage,
          creator_id: config.creator_id
        });
        
        // 使用完后清除
        localStorage.removeItem('selectedModelConfig');
      } catch (error) {
        console.error('解析存储的模型配置失败:', error);
      }
    }
    
    if (storedImage) {
      try {
        const image = JSON.parse(storedImage);
        setSelectedImage(image);
        
        // 自动填充镜像相关字段
        form.setFieldsValue({
          imageId: image.id,
          image: `${image.name}:${image.version}`,
          cluster: image.cluster
        });
        
        // 使用完后清除
        localStorage.removeItem('selectedImage');
      } catch (error) {
        console.error('解析存储的镜像失败:', error);
      }
    }
  }, [form]);

  // 处理模型配置选择
  const handleModelConfigChange = (configId) => {
    const config = modelConfigs.find(c => c.id === configId);
    setSelectedConfig(config);
    
    if (config) {
      // 将gpuCount转换为gpuIds数组
      const gpuIds = config.gpuIds || 
        (config.gpuCount ? Array.from({length: config.gpuCount}, (_, i) => i) : [0]);
      
      // 自动填充表单
      form.setFieldsValue({
        modelName: config.modelName,
        backend: config.backend,
        modelPath: config.modelPath,
        cluster: config.cluster,
        node: config.node,
        gpuIds: gpuIds,
        memoryUsage: config.memoryUsage,
        creator_id: config.creator_id
      });
    }
  };

  // 处理镜像选择
  const handleImageChange = (imageId) => {
    const image = images.find(img => img.id === imageId);
    setSelectedImage(image);
    
    if (image) {
      // 自动填充镜像相关字段
      form.setFieldsValue({
        image: `${image.name}:${image.version}`,
        cluster: image.cluster // 可选：根据镜像自动设置集群
      });
    }
  };

  // 提交表单
  const handleSubmit = async (values) => {
    setSubmitting(true);
    try {
      // 构建部署请求数据
      const deployData = {
        ...values,
        deployTime: new Date().toISOString(),
        status: 'pending'
      };

      const response = await fetch('http://127.0.0.1:5000/api/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(deployData),
      });

      const result = await response.json();
      
      if (result.status === 'success') {
        message.success('模型部署请求提交成功！');
        form.resetFields();
        setSelectedConfig(null);
        setSelectedImage(null);
      } else {
        message.error(result.message || '提交失败');
      }
    } catch (error) {
      console.error('提交部署请求失败:', error);
      message.error('提交失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  };

  // 重置表单
  const handleReset = () => {
    form.resetFields();
    setSelectedConfig(null);
    setSelectedImage(null);
  };

  return (
    <div className="model-deploy-container" style={{ padding: '20px' }}>
      <Card title={<Title level={2}>模型部署</Title>} bordered={false}>
        <Spin spinning={loading || submitting}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{
              gpuCount: 1,
              memoryUsage: 16
            }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Card 
                  title={<span><SettingOutlined /> 选择模型配置</span>} 
                  bordered={false} 
                  style={{ marginBottom: 16 }}
                >
                  <Form.Item
                    label="模型配置"
                    name="configId"
                  >
                    <Select
                      placeholder="选择一个已有的模型配置"
                      onChange={handleModelConfigChange}
                      allowClear
                      showSearch
                      optionFilterProp="children"
                    >
                      {modelConfigs.map(config => (
                        <Option key={config.id} value={config.id}>{config.modelName} ({config.backend})</Option>
                      ))}
                    </Select>
                  </Form.Item>
                  
                  {selectedConfig && (
                    <div className="selected-config-info">
                      <Divider orientation="left">已选配置</Divider>
                      <p><strong>模型名称:</strong> {selectedConfig.modelName}</p>
                      <p><strong>后端:</strong> {selectedConfig.backend}</p>
                      <p><strong>集群:</strong> {selectedConfig.cluster}</p>
                      <p><strong>GPU数量:</strong> {selectedConfig.gpuCount}</p>
                    </div>
                  )}
                </Card>
              </Col>
              
              <Col span={12}>
                <Card 
                  title={<span><CloudOutlined /> 选择镜像</span>} 
                  bordered={false} 
                  style={{ marginBottom: 16 }}
                >
                  <Form.Item
                    label="镜像"
                    name="imageId"
                  >
                    <Select
                      placeholder="选择一个镜像"
                      onChange={handleImageChange}
                      allowClear
                      showSearch
                      optionFilterProp="children"
                    >
                      {images.map(image => (
                        <Option key={image.id} value={image.id}>{image.name}:{image.version} ({image.cluster})</Option>
                      ))}
                    </Select>
                  </Form.Item>
                  
                  {selectedImage && (
                    <div className="selected-image-info">
                      <Divider orientation="left">已选镜像</Divider>
                      <p><strong>镜像名称:</strong> {selectedImage.name}</p>
                      <p><strong>版本:</strong> {selectedImage.version}</p>
                      <p><strong>集群:</strong> {selectedImage.cluster}</p>
                      <p><strong>大小:</strong> {selectedImage.size}</p>
                    </div>
                  )}
                </Card>
              </Col>
            </Row>
            
            <Card 
              title={<span><DeploymentUnitOutlined /> 部署参数</span>} 
              bordered={false}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="modelName"
                    label="模型名称"
                    rules={[{ required: true, message: '请输入模型名称' }]}
                  >
                    <Input placeholder="请输入模型名称" />
                  </Form.Item>
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="version"
                    label="部署版本"
                    rules={[{ required: true, message: '请输入部署版本' }]}
                  >
                    <Input placeholder="请输入部署版本，例如：v1.0" />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={16}>
                <Col span={12}>
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
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="image"
                    label="镜像名"
                    rules={[{ required: true, message: '请输入镜像名' }]}
                  >
                    <Input placeholder="请输入镜像名，例如：vllm_image:v3" />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="cluster"
                    label="部署集群"
                    rules={[{ required: true, message: '请选择部署集群' }]}
                  >
                    <Select placeholder="请选择部署集群">
                      {clusters.map(cluster => (
                        <Option key={cluster} value={cluster}>{cluster}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="node"
                    label="部署节点"
                    rules={[{ required: true, message: '请选择部署节点' }]}
                  >
                    <Select placeholder="请选择部署节点">
                      {nodes.map(node => (
                        <Option key={node} value={node}>{node}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={16}>
                <Col span={12}>
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
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="memoryUsage"
                    label={<span>显存占用(GB) <Tooltip title="每个GPU分配的显存大小"><InfoCircleOutlined /></Tooltip></span>}
                    rules={[{ required: true, message: '请输入显存占用量' }]}
                  >
                    <InputNumber min={1} max={80} placeholder="请输入显存占用量(GB)" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item
                name="modelPath"
                label="模型路径"
                rules={[{ required: true, message: '请输入模型路径' }]}
              >
                <Input placeholder="请输入模型路径，例如：/mnt/models/llama-7b" />
              </Form.Item>
              
              <Form.Item
                name="description"
                label="部署描述"
              >
                <TextArea rows={4} placeholder="请输入部署描述信息" />
              </Form.Item>
              
              <Form.Item
                name="creator_id"
                label="创建者ID"
                rules={[{ required: true, message: '请输入创建者ID' }]}
              >
                <Input placeholder="请输入创建者ID" />
              </Form.Item>
            </Card>
            
            <Form.Item style={{ marginTop: 16, textAlign: 'center' }}>
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={submitting} style={{ marginRight: 8 }}>
                提交部署
              </Button>
              <Button icon={<ClearOutlined />} onClick={handleReset}>
                重置
              </Button>
            </Form.Item>
          </Form>
        </Spin>
      </Card>
    </div>
  );
};

export default ModelDeployForm;
