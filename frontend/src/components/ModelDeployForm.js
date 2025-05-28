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
      // 使用后端API获取镜像列表
      const response = await fetch('http://127.0.0.1:5000/api/images');
      const result = await response.json();
      
      if (result.status === 'success' && result.data) {
        console.log('获取镜像数据成功:', result.data);
        setImages(result.data);
      } else {
        console.error('获取镜像列表失败:', result.message);
        setImages([]);
      }
    } catch (error) {
      console.error('获取镜像列表失败:', error);
      // 如果获取失败，使用空数组
      setImages([]);
    }
  };

  // 获取集群列表
  const fetchClusters = async () => {
    try {
      // 使用中心控制器的API获取实际集群列表
      const response = await fetch('http://localhost:5001/api/clusters');
      const result = await response.json();
      
      if (result.status === 'success' && result.data) {
        // 将集群数据转换为适合下拉框的格式
        const clusterList = result.data.map(cluster => ({
          id: cluster.id,
          name: cluster.name,
          adapter_type: cluster.adapter_type
        }));
        setClusters(clusterList);
      } else {
        console.error('获取集群列表失败:', result.message);
        // 如果获取失败，使用默认数据
        setClusters([]);
      }
    } catch (error) {
      console.error('获取集群列表失败:', error);
      setClusters([]);
    }
  };

  // 获取节点列表
  const fetchNodes = async (clusterId = null) => {
    try {
      if (!clusterId) {
        // 如果没有指定集群ID，清空节点列表
        setNodes([]);
        return;
      }
      
      // 使用中心控制器的API获取指定集群的节点列表
      const response = await fetch(`http://localhost:5001/api/clusters/${clusterId}/nodes`);
      const result = await response.json();
      
      if (result.status === 'success' && result.data) {
        // 将节点数据转换为适合下拉框的格式
        const nodeList = result.data.map(node => ({
          id: node.id,
          name: node.name,
          status: node.status
        }));
        setNodes(nodeList);
      } else {
        console.error('获取节点列表失败:', result.message);
        setNodes([]);
      }
    } catch (error) {
      console.error('获取节点列表失败:', error);
      setNodes([]);
    }
  };

  // 初始化加载数据
  useEffect(() => {
    fetchModelConfigs();
    fetchImages();
    fetchClusters();
    // 初始时不加载节点列表，等待选择集群后加载
    
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
      // 自动填充表单，包括镜像信息
      const formValues = {
        modelName: config.modelName,
        backend: config.backend,
        modelPath: config.ossPath || 'oss://model_files/default.tar',
        gpuCount: config.gpuCount || 1, // 直接使用gpuCount，如果没有则默认为1
        memoryUsage: config.memoryUsage
      };
      
      // 如果模型配置中有镜像信息，也填充镜像字段
      // 注意：后端返回的是'image'而不是'image_id'
      if (config.image) {
        // 使用image作为image_id
        formValues.image_id = config.image;
        
        // 如果有image_name并且不是"未知镜像"，则使用它
        // 否则使用image字段作为镜像名
        if (config.image_name && config.image_name !== '未知镜像') {
          formValues.image_name = config.image_name;
        } else {
          formValues.image_name = config.image;
        }
        
        // 尝试在镜像列表中找到对应的镜像
        const image = images.find(img => `${img.name}:${img.version}` === config.image || img.id === config.image);
        if (image) {
          setSelectedImage(image);
          formValues.image_id = image.id;
          formValues.image_name = `${image.name}:${image.version}`;
        }
      }
      
      form.setFieldsValue(formValues);
    }
  };

  // 处理镜像选择
  const handleImageChange = (imageId) => {
    const image = images.find(img => img.id === imageId);
    setSelectedImage(image);
    
    if (image) {
      // 自动填充镜像相关字段，只显示镜像名称和版本
      form.setFieldsValue({
        image_id: image.id,
        image_name: `${image.name}:${image.version}`
      });
    }
  };

  // 提交表单
  const handleSubmit = async (values) => {
    setSubmitting(true);
    try {
      // 构建部署请求数据
      const { image_name, ...otherValues } = values; // 移除image_name字段，它只用于显示
      const deployData = {
        ...otherValues,
        // 将gpuCount转换为整数
        gpuCount: parseInt(values.gpuCount, 10),
        // 确保使用正确的集群名称
        cluster: 'gpt4',  // 使用已注册的集群名称
        deployTime: new Date().toISOString(),
        status: 'pending'
      };

      // 提交到应用服务器（端口5000）
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
              gpuCount: 1, // 默认GPU数量为1
              memoryUsage: 16
            }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Card 
                  title={<span><SettingOutlined /> 选择模型配置</span>} 
                  bordered={false} 
                  style={{ marginBottom: 16, width: '100%' }}
                  bodyStyle={{ borderBottom: 'none' }}
                >
                  <Form.Item
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
                        <Option key={config.id} value={config.id}>{config.modelName}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                  

                </Card>
              </Col>
              
              <Col span={12}>
                <Card 
                  title={<span><CloudOutlined /> 选择镜像</span>} 
                  bordered={false} 
                  style={{ marginBottom: 16, width: '100%' }}
                  bodyStyle={{ borderBottom: 'none' }}
                >
                  <Form.Item
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
                        <Option key={image.id} value={image.id}>{image.name}:{image.version}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                  

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
                      <Option value="transformers">transformers</Option>
                    </Select>
                  </Form.Item>
                </Col>
                
                <Col span={12}>
                  <Form.Item
                    name="image_id"
                    label="镜像"
                    rules={[{ required: true, message: '请选择镜像' }]}
                    hidden
                  >
                    <Input />
                  </Form.Item>
                  <Form.Item
                    name="image_name"
                    label="镜像"
                    rules={[{ required: true, message: '请选择镜像' }]}
                  >
                    <Input placeholder="请先选择镜像" disabled />
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
                    <Select 
                      placeholder="请选择部署集群"
                      onChange={(value) => {
                        // 当选择集群时，获取该集群的节点列表
                        const selectedCluster = clusters.find(c => c.id === value);
                        if (selectedCluster) {
                          fetchNodes(selectedCluster.id);
                          // 清空已选节点
                          form.setFieldsValue({ node: undefined });
                        }
                      }}
                    >
                      {clusters.map(cluster => (
                        <Option key={cluster.id} value={cluster.id}>
                          {cluster.name} ({cluster.adapter_type})
                        </Option>
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
                    <Select 
                      placeholder="请选择部署节点"
                      disabled={!form.getFieldValue('cluster')} // 如果没有选择集群，禁用节点选择
                    >
                      {nodes.map(node => (
                        <Option key={node.id} value={node.id}>
                          {node.name} ({node.status === 'online' ? '在线' : '离线'})
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="gpuCount"
                    label="GPU数量"
                    rules={[{ required: true, message: '请输入所需GPU数量' }]}
                  >
                    <InputNumber 
                      min={1} 
                      max={8} 
                      placeholder="请输入所需GPU数量" 
                      style={{ width: '100%' }} 
                    />
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
                <Input placeholder="请输入模型路径，例如：oss://model_files/qwen_cpt_vllm.tar" />
              </Form.Item>
              
              <Form.Item
                name="description"
                label="部署描述"
              >
                <TextArea rows={4} placeholder="请输入部署描述信息" />
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
