import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Typography, Row, Col, Spin, Tabs, Divider } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined, UserAddOutlined, MailOutlined, PhoneOutlined, TeamOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;
const { TabPane } = Tabs;

const Login = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      // 调用登录API
      const response = await fetch('http://127.0.0.1:5000/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: values.username,
          password: values.password,
        }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        message.success('登录成功！');
        
        // 存储用户信息和token到localStorage
        localStorage.setItem('user', JSON.stringify(data.data.user));
        localStorage.setItem('token', data.data.token);
        
        // 调用登录成功回调
        if (onLoginSuccess) {
          onLoginSuccess(data.data.user);
        }
        
        // 跳转到首页
        navigate('/');
      } else {
        message.error(data.message || '登录失败，请检查用户名和密码');
      }
    } catch (error) {
      console.error('登录请求失败:', error);
      message.error('登录失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 注册处理函数
  const onRegister = async (values) => {
    setLoading(true);
    try {
      // 检查两次密码是否一致
      if (values.password !== values.confirmPassword) {
        message.error('两次输入的密码不一致');
        setLoading(false);
        return;
      }

      // 调用注册API
      const response = await fetch('http://127.0.0.1:5000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: values.username,
          password: values.password,
          email: values.email,
          phone: values.phone,
          department: values.department
        }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        message.success('注册成功！请登录');
        setActiveTab('login');
        form.resetFields();
      } else {
        message.error(data.message || '注册失败');
      }
    } catch (error) {
      console.error('注册请求失败:', error);
      message.error('注册失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 切换标签页
  const handleTabChange = (key) => {
    setActiveTab(key);
    form.resetFields();
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: 'calc(100vh - 64px)',
      background: '#f0f2f5'
    }}>
      <Spin spinning={loading}>
        <Card style={{ width: 450, boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }}>
          <Tabs activeKey={activeTab} onChange={handleTabChange} centered>
            <TabPane tab="登录" key="login">
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <Title level={3}>用户登录</Title>
              </div>
              
              <Form
                name="login_form"
                initialValues={{ remember: true }}
                onFinish={onFinish}
                size="large"
                form={form}
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                >
                  <Input 
                    prefix={<UserOutlined />} 
                    placeholder="用户名" 
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                >
                  <Input.Password 
                    prefix={<LockOutlined />} 
                    placeholder="密码" 
                  />
                </Form.Item>

                <Form.Item>
                  <Row justify="space-between">
                    <Col>
                      <a href="#forgot">忘记密码？</a>
                    </Col>
                    <Col>
                      <a onClick={() => setActiveTab('register')}>注册账号</a>
                    </Col>
                  </Row>
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    icon={<LoginOutlined />}
                    loading={loading && activeTab === 'login'}
                    block
                  >
                    登录
                  </Button>
                </Form.Item>
              </Form>
            </TabPane>
            
            <TabPane tab="注册" key="register">
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <Title level={3}>用户注册</Title>
              </div>
              
              <Form
                name="register_form"
                onFinish={onRegister}
                size="large"
                form={form}
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                >
                  <Input 
                    prefix={<UserOutlined />} 
                    placeholder="用户名" 
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码' },
                          { min: 6, message: '密码长度不能少于6个字符' }]}
                >
                  <Input.Password 
                    prefix={<LockOutlined />} 
                    placeholder="密码" 
                  />
                </Form.Item>

                <Form.Item
                  name="confirmPassword"
                  rules={[{ required: true, message: '请确认密码' },
                          ({ getFieldValue }) => ({
                            validator(_, value) {
                              if (!value || getFieldValue('password') === value) {
                                return Promise.resolve();
                              }
                              return Promise.reject(new Error('两次输入的密码不一致'));
                            },
                          })]}
                >
                  <Input.Password 
                    prefix={<LockOutlined />} 
                    placeholder="确认密码" 
                  />
                </Form.Item>

                <Form.Item
                  name="email"
                  rules={[{ required: true, message: '请输入邮箱' },
                          { type: 'email', message: '请输入有效的邮箱地址' }]}
                >
                  <Input 
                    prefix={<MailOutlined />} 
                    placeholder="邮箱" 
                  />
                </Form.Item>

                <Form.Item
                  name="phone"
                  rules={[{ required: true, message: '请输入手机号' },
                          { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }]}
                >
                  <Input 
                    prefix={<PhoneOutlined />} 
                    placeholder="手机号" 
                  />
                </Form.Item>

                <Form.Item
                  name="department"
                  rules={[{ required: true, message: '请输入部门' }]}
                >
                  <Input 
                    prefix={<TeamOutlined />} 
                    placeholder="部门" 
                  />
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    icon={<UserAddOutlined />}
                    loading={loading && activeTab === 'register'}
                    block
                  >
                    注册
                  </Button>
                </Form.Item>

                <Form.Item>
                  <div style={{ textAlign: 'center' }}>
                    <span>已有账号？</span>
                    <a onClick={() => setActiveTab('login')}>立即登录</a>
                  </div>
                </Form.Item>
              </Form>
            </TabPane>
          </Tabs>
        </Card>
      </Spin>
    </div>
  );
};

export default Login;
