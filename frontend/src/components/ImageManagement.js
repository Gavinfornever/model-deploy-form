import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, DatePicker, message, Space, Popconfirm, Typography, Tooltip } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, DeploymentUnitOutlined } from '@ant-design/icons';
import moment from 'moment';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

const ImageManagement = () => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingImage, setEditingImage] = useState(null);
  const [form] = Form.useForm();
  const [searchText, setSearchText] = useState('');
  
  // 处理使用镜像部署
  const handleDeployWithImage = (image) => {
    // 使用 localStorage 临时存储选中的镜像，以便在部署页面使用
    localStorage.setItem('selectedImage', JSON.stringify(image));
    // 跳转到部署页面
    window.location.href = '/deploy';
  };

  // 模拟数据
  const mockImages = [
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
    {
      id: 3,
      name: 'pytorch_image',
      version: 'v2.1',
      cluster: 'muxi集群',
      size: '4.5GB',
      createDate: '2025-04-12',
      creator: '王五'
    },
    {
      id: 4,
      name: 'tensorflow_image',
      version: 'v2.0',
      cluster: 'A100集群',
      size: '6.1GB',
      createDate: '2025-04-08',
      creator: '赵六'
    },
    {
      id: 5,
      name: 'llama_image',
      version: 'v2',
      cluster: 'A100集群',
      size: '8.3GB',
      createDate: '2025-04-05',
      creator: '张三'
    },
    {
      id: 6,
      name: 'bert_image',
      version: 'v1.5',
      cluster: 'A10集群',
      size: '2.7GB',
      createDate: '2025-04-18',
      creator: '李四'
    },
    {
      id: 7,
      name: 'gpt_image',
      version: 'v3.5',
      cluster: 'A100集群',
      size: '9.2GB',
      createDate: '2025-04-03',
      creator: '王五'
    },
    {
      id: 8,
      name: 'stable_diffusion_image',
      version: 'v2.1',
      cluster: 'A100集群',
      size: '7.5GB',
      createDate: '2025-04-07',
      creator: '赵六'
    },
    {
      id: 9,
      name: 'milvus_image',
      version: 'v2.2',
      cluster: 'muxi集群',
      size: '3.2GB',
      createDate: '2025-04-14',
      creator: '张三'
    },
    {
      id: 10,
      name: 'faiss_image',
      version: 'v1.7',
      cluster: 'muxi集群',
      size: '2.1GB',
      createDate: '2025-04-16',
      creator: '李四'
    },
    {
      id: 11,
      name: 'onnx_image',
      version: 'v1.14',
      cluster: 'A10集群',
      size: '1.8GB',
      createDate: '2025-04-19',
      creator: '王五'
    },
    {
      id: 12,
      name: 'triton_image',
      version: 'v2.3',
      cluster: 'A100集群',
      size: '4.3GB',
      createDate: '2025-04-11',
      creator: '赵六'
    },
    {
      id: 13,
      name: 'cuda_image',
      version: 'v12.1',
      cluster: 'A100集群',
      size: '5.7GB',
      createDate: '2025-04-09',
      creator: '张三'
    },
    {
      id: 14,
      name: 'cudnn_image',
      version: 'v8.9',
      cluster: 'A100集群',
      size: '4.9GB',
      createDate: '2025-04-06',
      creator: '李四'
    },
    {
      id: 15,
      name: 'jupyter_image',
      version: 'v7.0',
      cluster: 'muxi集群',
      size: '2.3GB',
      createDate: '2025-04-17',
      creator: '王五'
    },
    {
      id: 16,
      name: 'ray_image',
      version: 'v2.5',
      cluster: 'A10集群',
      size: '3.6GB',
      createDate: '2025-04-13',
      creator: '赵六'
    },
    {
      id: 17,
      name: 'langchain_image',
      version: 'v0.8',
      cluster: 'muxi集群',
      size: '1.5GB',
      createDate: '2025-04-20',
      creator: '张三'
    },
    {
      id: 18,
      name: 'transformers_image',
      version: 'v4.30',
      cluster: 'A10集群',
      size: '3.1GB',
      createDate: '2025-04-04',
      creator: '李四'
    },
    {
      id: 19,
      name: 'deepspeed_image',
      version: 'v0.9',
      cluster: 'A100集群',
      size: '4.2GB',
      createDate: '2025-04-02',
      creator: '王五'
    },
    {
      id: 20,
      name: 'accelerate_image',
      version: 'v0.21',
      cluster: 'A10集群',
      size: '1.9GB',
      createDate: '2025-04-01',
      creator: '赵六'
    },
    {
      id: 21,
      name: 'diffusers_image',
      version: 'v0.18',
      cluster: 'A100集群',
      size: '5.5GB',
      createDate: '2025-03-30',
      creator: '张三'
    },
    {
      id: 22,
      name: 'bitsandbytes_image',
      version: 'v0.40',
      cluster: 'muxi集群',
      size: '1.2GB',
      createDate: '2025-03-28',
      creator: '李四'
    }
  ];

  // 获取镜像列表
  const fetchImages = async () => {
    setLoading(true);
    try {
      // 实际项目中应该调用后端API
      // const response = await axios.get('/api/images');
      // setImages(response.data);
      
      // 使用模拟数据
      setTimeout(() => {
        setImages(mockImages);
        setLoading(false);
      }, 500);
    } catch (error) {
      console.error('获取镜像列表失败:', error);
      message.error('获取镜像列表失败');
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    fetchImages();
  }, []);

  // 添加或更新镜像
  const handleSaveImage = async (values) => {
    try {
      if (editingImage) {
        // 更新镜像
        // await axios.put(`/api/images/${editingImage.id}`, values);
        
        // 模拟更新
        const updatedImages = images.map(img => 
          img.id === editingImage.id ? { ...img, ...values } : img
        );
        setImages(updatedImages);
        message.success('镜像更新成功');
      } else {
        // 添加镜像
        // await axios.post('/api/images', values);
        
        // 模拟添加
        const newImage = {
          id: Math.max(...images.map(img => img.id), 0) + 1,
          ...values,
          createDate: values.createDate.format('YYYY-MM-DD')
        };
        setImages([...images, newImage]);
        message.success('镜像添加成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingImage(null);
    } catch (error) {
      console.error('保存镜像失败:', error);
      message.error('保存镜像失败');
    }
  };

  // 删除镜像
  const handleDeleteImage = async (id) => {
    try {
      // await axios.delete(`/api/images/${id}`);
      
      // 模拟删除
      const updatedImages = images.filter(img => img.id !== id);
      setImages(updatedImages);
      message.success('镜像删除成功');
    } catch (error) {
      console.error('删除镜像失败:', error);
      message.error('删除镜像失败');
    }
  };

  // 编辑镜像
  const handleEditImage = (record) => {
    setEditingImage(record);
    form.setFieldsValue({
      ...record,
      createDate: moment(record.createDate)
    });
    setModalVisible(true);
  };

  // 添加新镜像
  const handleAddImage = () => {
    setEditingImage(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 搜索过滤
  const filteredImages = images.filter(
    img => 
      img.name.toLowerCase().includes(searchText.toLowerCase()) ||
      img.version.toLowerCase().includes(searchText.toLowerCase()) ||
      img.cluster.includes(searchText) ||
      img.creator.includes(searchText)
  );

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '镜像名称',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      sorter: (a, b) => a.version.localeCompare(b.version),
    },
    {
      title: '所在集群',
      dataIndex: 'cluster',
      key: 'cluster',
      filters: [
        { text: 'muxi集群', value: 'muxi集群' },
        { text: 'A10集群', value: 'A10集群' },
        { text: 'A100集群', value: 'A100集群' },
      ],
      onFilter: (value, record) => record.cluster === value,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      sorter: (a, b) => {
        const sizeA = parseFloat(a.size.replace('GB', ''));
        const sizeB = parseFloat(b.size.replace('GB', ''));
        return sizeA - sizeB;
      },
    },
    {
      title: '创建日期',
      dataIndex: 'createDate',
      key: 'createDate',
      sorter: (a, b) => moment(a.createDate).unix() - moment(b.createDate).unix(),
    },
    {
      title: '创建者',
      dataIndex: 'creator',
      key: 'creator',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            icon={<DeploymentUnitOutlined />} 
            size="small"
            onClick={() => handleDeployWithImage(record)}
          >
            部署
          </Button>
          <Button 
            type="default" 
            icon={<EditOutlined />} 
            size="small"
            onClick={() => handleEditImage(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个镜像吗？"
            onConfirm={() => handleDeleteImage(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="primary" 
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

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>镜像管理</Title>
        <div>
          <Input
            placeholder="搜索镜像"
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            style={{ width: 200, marginRight: 16 }}
            prefix={<SearchOutlined />}
          />
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleAddImage}
          >
            添加镜像
          </Button>
        </div>
      </div>
      
      <Table
        columns={columns}
        dataSource={filteredImages}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
        bordered
      />

      {/* 添加/编辑镜像的模态框 */}
      <Modal
        title={editingImage ? '编辑镜像' : '添加镜像'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveImage}
          initialValues={{ cluster: 'muxi集群' }}
        >
          <Form.Item
            name="name"
            label="镜像名称"
            rules={[{ required: true, message: '请输入镜像名称' }]}
          >
            <Input placeholder="请输入镜像名称" />
          </Form.Item>
          
          <Form.Item
            name="version"
            label="版本"
            rules={[{ required: true, message: '请输入版本' }]}
          >
            <Input placeholder="请输入版本，例如：v1.0" />
          </Form.Item>
          
          <Form.Item
            name="cluster"
            label="所在集群"
            rules={[{ required: true, message: '请选择所在集群' }]}
          >
            <Select placeholder="请选择所在集群">
              <Option value="muxi集群">muxi集群</Option>
              <Option value="A10集群">A10集群</Option>
              <Option value="A100集群">A100集群</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="size"
            label="大小"
            rules={[{ required: true, message: '请输入大小' }]}
          >
            <Input placeholder="请输入大小，例如：5.2GB" />
          </Form.Item>
          
          <Form.Item
            name="createDate"
            label="创建日期"
            rules={[{ required: true, message: '请选择创建日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="creator"
            label="创建者"
            rules={[{ required: true, message: '请输入创建者' }]}
          >
            <Input placeholder="请输入创建者" />
          </Form.Item>
          
          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button 
                style={{ marginRight: 8 }} 
                onClick={() => {
                  setModalVisible(false);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ImageManagement;
