import React, { useState, useEffect } from 'react';
import { 
  Form, Input, Button, Card, Select, message, 
  Upload, Space, Divider, Typography, Steps, Result 
} from 'antd';
import { 
  UploadOutlined, ClusterOutlined, 
  CloudServerOutlined, CheckCircleOutlined 
} from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;

const ClusterRegistration = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [registrationResult, setRegistrationResult] = useState(null);
  const [authMethod, setAuthMethod] = useState('password');
  const [keyFile, setKeyFile] = useState(null);

  // 集群注册步骤
  const steps = [
    {
      title: '基本信息',
      content: '输入集群基本信息',
    },
    {
      title: '连接配置',
      content: '配置集群连接信息',
    },
    {
      title: '确认提交',
      content: '确认并提交集群信息',
    },
    {
      title: '完成',
      content: '集群注册完成',
    },
  ];

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      // 构建请求数据
      const formData = new FormData();
      
      // 添加基本信息
      const clusterData = {
        name: values.name,
        adapter_type: values.adapter_type,
        center_node_ip: values.center_node_ip,
        center_node_port: values.center_node_port || 22,
        center_controller_url: window.location.origin,
        internal_ip: values.internal_ip
      };
      
      // 添加认证信息
      if (authMethod === 'password') {
        clusterData.username = values.username;
        clusterData.password = values.password;
      } else if (authMethod === 'key' && keyFile) {
        clusterData.username = values.username;
        formData.append('key_file', keyFile);
      }

      // 将集群数据转换为JSON并添加到表单
      formData.append('cluster_data', JSON.stringify(clusterData));

      // 获取认证令牌
      const token = localStorage.getItem('token');
      
      // 发送请求
      const response = await axios.post(
        'http://localhost:5000/api/clusters', 
        authMethod === 'key' ? formData : clusterData,
        {
          headers: {
            'Content-Type': authMethod === 'key' ? 'multipart/form-data' : 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.data.status === 'success') {
        setRegistrationResult(response.data);
        message.success('集群注册成功！');
        setCurrentStep(3); // 直接跳到完成步骤
      } else {
        message.error(`注册失败: ${response.data.message}`);
      }
    } catch (error) {
      console.error('注册失败:', error);
      message.error('集群注册失败，请检查输入信息');
    } finally {
      setLoading(false);
    }
  };

  // 处理步骤变化
  const handleStepChange = (step) => {
    if (step < currentStep) {
      setCurrentStep(step);
      return;
    }

    form.validateFields()
      .then(() => {
        if (step === 2) {
          // 确认提交
          handleSubmit();
        } else {
          setCurrentStep(step);
        }
      })
      .catch(error => {
        console.error('表单验证失败:', error);
      });
  };

  // 处理认证方式变化
  const handleAuthMethodChange = (value) => {
    setAuthMethod(value);
  };

  // 处理密钥文件上传
  const handleKeyFileUpload = (info) => {
    if (info.file.status === 'done') {
      setKeyFile(info.file.originFileObj);
      message.success(`${info.file.name} 上传成功`);
    } else if (info.file.status === 'error') {
      message.error(`${info.file.name} 上传失败`);
    }
  };

  // 渲染基本信息表单
  const renderBasicInfoForm = () => (
    <Card title="集群基本信息" bordered={false}>
      <Form.Item
        name="name"
        label="集群名称"
        rules={[{ required: true, message: '请输入集群名称' }]}
      >
        <Input placeholder="例如: 本地开发集群" prefix={<ClusterOutlined />} />
      </Form.Item>

      <Form.Item
        name="adapter_type"
        label="集群类型"
        rules={[{ required: true, message: '请选择集群类型' }]}
        initialValue="apple"
      >
        <Select>
          <Option value="apple">Apple Silicon</Option>
          <Option value="nvidia">NVIDIA</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="description"
        label="集群描述"
      >
        <Input.TextArea rows={3} placeholder="可选，输入集群的描述信息" />
      </Form.Item>
    </Card>
  );

  // 渲染连接配置表单
  const renderConnectionForm = () => (
    <Card title="集群连接配置" bordered={false}>
      <Form.Item
        name="center_node_ip"
        label="集群中心节点IP"
        rules={[{ required: true, message: '请输入集群中心节点IP' }]}
        tooltip="集群中心节点的外部连接地址，用于部署集群控制器"
      >
        <Input placeholder="例如: 192.168.1.100" />
      </Form.Item>

      <Form.Item
        name="center_node_port"
        label="SSH端口"
        initialValue={22}
        rules={[{ required: true, message: '请输入SSH端口' }]}
      >
        <Input type="number" min={1} max={65535} />
      </Form.Item>

      <Form.Item
        name="internal_ip"
        label="内部网络地址"
        tooltip="集群内部主节点的内网地址，用于集群内部通信"
        rules={[{ required: true, message: '请输入内部网络地址' }]}
      >
        <Input placeholder="例如: 10.0.0.1" />
      </Form.Item>

      <Form.Item
        name="auth_method"
        label="认证方式"
        initialValue="password"
      >
        <Select onChange={handleAuthMethodChange}>
          <Option value="password">密码认证</Option>
          <Option value="key">密钥认证</Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="username"
        label="用户名"
        rules={[{ required: true, message: '请输入用户名' }]}
        initialValue="root"
      >
        <Input placeholder="例如: root" />
      </Form.Item>

      {authMethod === 'password' ? (
        <Form.Item
          name="password"
          label="密码"
          rules={[{ required: authMethod === 'password', message: '请输入密码' }]}
        >
          <Input.Password placeholder="输入SSH密码" />
        </Form.Item>
      ) : (
        <Form.Item
          name="key_file"
          label="SSH密钥文件"
          rules={[{ required: authMethod === 'key', message: '请上传SSH密钥文件' }]}
        >
          <Upload
            name="key_file"
            beforeUpload={() => false}
            onChange={handleKeyFileUpload}
          >
            <Button icon={<UploadOutlined />}>选择密钥文件</Button>
          </Upload>
        </Form.Item>
      )}
    </Card>
  );

  // 渲染确认信息
  const renderConfirmation = () => (
    <Card title="确认集群信息" bordered={false}>
      <Paragraph>
        <Text strong>集群名称:</Text> {form.getFieldValue('name')}
      </Paragraph>
      <Paragraph>
        <Text strong>集群类型:</Text> {form.getFieldValue('adapter_type') === 'apple' ? 'Apple Silicon' : 'NVIDIA'}
      </Paragraph>
      <Paragraph>
        <Text strong>中心节点IP:</Text> {form.getFieldValue('center_node_ip')}
      </Paragraph>
      <Paragraph>
        <Text strong>SSH端口:</Text> {form.getFieldValue('center_node_port')}
      </Paragraph>
      <Paragraph>
        <Text strong>内部网络地址:</Text> {form.getFieldValue('internal_ip')}
      </Paragraph>
      <Paragraph>
        <Text strong>认证方式:</Text> {authMethod === 'password' ? '密码认证' : '密钥认证'}
      </Paragraph>
      <Paragraph>
        <Text strong>用户名:</Text> {form.getFieldValue('username')}
      </Paragraph>

      <Divider />
      <Paragraph>
        <Text type="warning">
          注意: 点击"提交"按钮后，系统将连接到集群中心节点，部署集群控制器，并自动发现集群资源。
          这个过程可能需要几分钟时间，请耐心等待。
        </Text>
      </Paragraph>
    </Card>
  );

  // 渲染完成信息
  const renderCompletion = () => (
    <Result
      status="success"
      title="集群注册成功！"
      subTitle={`集群ID: ${registrationResult?.data?.cluster_id || '未知'}`}
      extra={[
        <Button 
          type="primary" 
          key="console" 
          onClick={() => window.location.href = '/clusters'}
        >
          查看集群列表
        </Button>,
        <Button key="register" onClick={() => {
          form.resetFields();
          setCurrentStep(0);
          setRegistrationResult(null);
        }}>
          注册新集群
        </Button>,
      ]}
    />
  );

  // 根据当前步骤渲染内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderBasicInfoForm();
      case 1:
        return renderConnectionForm();
      case 2:
        return renderConfirmation();
      case 3:
        return renderCompletion();
      default:
        return null;
    }
  };

  return (
    <div className="cluster-registration">
      <Title level={2}>
        <CloudServerOutlined /> 集群注册
      </Title>
      
      <Paragraph>
        通过以下步骤注册新的计算集群，系统将自动发现集群资源并进行注册。
      </Paragraph>
      
      <Steps current={currentStep} onChange={handleStepChange}>
        {steps.map(item => (
          <Step key={item.title} title={item.title} />
        ))}
      </Steps>
      
      <div className="steps-content" style={{ marginTop: 24, marginBottom: 24 }}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            adapter_type: 'apple',
            center_node_port: 22,
            auth_method: 'password',
            username: 'root'
          }}
        >
          {renderStepContent()}
        </Form>
      </div>
      
      <div className="steps-action">
        {currentStep > 0 && currentStep < 3 && (
          <Button style={{ marginRight: 8 }} onClick={() => setCurrentStep(currentStep - 1)}>
            上一步
          </Button>
        )}
        
        {currentStep < 2 && (
          <Button type="primary" onClick={() => handleStepChange(currentStep + 1)}>
            下一步
          </Button>
        )}
        
        {currentStep === 2 && (
          <Button type="primary" loading={loading} onClick={handleSubmit}>
            提交
          </Button>
        )}
      </div>
    </div>
  );
};

export default ClusterRegistration;
