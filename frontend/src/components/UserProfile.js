import React, { useState, useEffect } from 'react';
import { 
  Card, Avatar, Typography, Tabs, Form, Input, Button, 
  message, Row, Col, Upload, Divider, Spin, Descriptions
} from 'antd';
import { 
  UserOutlined, MailOutlined, PhoneOutlined, LockOutlined, 
  EditOutlined, SaveOutlined, UploadOutlined, TeamOutlined,
  CalendarOutlined, IdcardOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const UserProfile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => {
    // 从localStorage获取用户信息
    const storedUser = localStorage.getItem('user');
    if (!storedUser) {
      message.error('请先登录');
      navigate('/login');
      return;
    }

    try {
      const parsedUser = JSON.parse(storedUser);
      setUser(parsedUser);
      
      // 设置表单初始值
      form.setFieldsValue({
        username: parsedUser.username,
        email: parsedUser.email,
        phone: parsedUser.phone,
        department: parsedUser.department,
        role: parsedUser.role
      });
    } catch (error) {
      console.error('解析用户信息失败:', error);
      message.error('获取用户信息失败');
      navigate('/login');
    } finally {
      setLoading(false);
    }
  }, [form, navigate]);

  // 更新用户信息
  const handleUpdateProfile = async (values) => {
    if (!user) return;
    
    setSaving(true);
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/users/${user.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(values)
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        message.success('个人信息更新成功');
        
        // 更新本地存储的用户信息
        const updatedUser = { ...user, ...values };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        setUser(updatedUser);
      } else {
        message.error(data.message || '更新失败');
      }
    } catch (error) {
      console.error('更新用户信息失败:', error);
      message.error('更新失败，请稍后重试');
    } finally {
      setSaving(false);
    }
  };

  // 修改密码
  const handleChangePassword = async (values) => {
    if (!user) return;
    
    setSaving(true);
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/users/${user.id}/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          oldPassword: values.oldPassword,
          newPassword: values.newPassword
        })
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        message.success('密码修改成功');
        passwordForm.resetFields();
      } else {
        message.error(data.message || '密码修改失败');
      }
    } catch (error) {
      console.error('修改密码失败:', error);
      message.error('修改密码失败，请稍后重试');
    } finally {
      setSaving(false);
    }
  };

  // 上传头像
  const handleAvatarUpload = async (info) => {
    if (info.file.status === 'uploading') {
      return;
    }
    
    if (info.file.status === 'done') {
      if (info.file.response.status === 'success') {
        const avatarUrl = info.file.response.data.url;
        
        // 更新用户头像
        const updatedUser = { ...user, avatar: avatarUrl };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        setUser(updatedUser);
        
        message.success('头像上传成功');
      } else {
        message.error(info.file.response.message || '头像上传失败');
      }
    } else if (info.file.status === 'error') {
      message.error('头像上传失败');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <Card>
        <Row gutter={24}>
          <Col span={6}>
            <div style={{ textAlign: 'center' }}>
              <Avatar 
                size={120} 
                src={user?.avatar} 
                icon={<UserOutlined />} 
                style={{ marginBottom: 16 }}
              />
              <Upload
                name="avatar"
                action="http://127.0.0.1:5000/api/users/avatar"
                headers={{ Authorization: `Bearer ${localStorage.getItem('token')}` }}
                showUploadList={false}
                onChange={handleAvatarUpload}
              >
                <Button icon={<UploadOutlined />}>更换头像</Button>
              </Upload>
              <Divider />
              <Title level={4}>{user?.username}</Title>
              <Text type="secondary">{user?.role}</Text>
              <Text type="secondary" style={{ display: 'block' }}>{user?.department}</Text>
            </div>
          </Col>
          
          <Col span={18}>
            <Tabs defaultActiveKey="profile">
              <TabPane tab="个人信息" key="profile">
                <Descriptions 
                  title="基本信息" 
                  bordered 
                  column={2}
                  style={{ marginBottom: 24 }}
                >
                  <Descriptions.Item label="用户名">{user?.username}</Descriptions.Item>
                  <Descriptions.Item label="邮箱">{user?.email}</Descriptions.Item>
                  <Descriptions.Item label="手机号">{user?.phone}</Descriptions.Item>
                  <Descriptions.Item label="部门">{user?.department}</Descriptions.Item>
                  <Descriptions.Item label="角色">{user?.role}</Descriptions.Item>
                  <Descriptions.Item label="账号状态">
                    {user?.status === 'active' ? '正常' : '禁用'}
                  </Descriptions.Item>
                  <Descriptions.Item label="创建时间">{user?.createTime}</Descriptions.Item>
                  <Descriptions.Item label="最后登录">{user?.lastLogin}</Descriptions.Item>
                </Descriptions>
                
                <Card title="编辑个人信息" style={{ marginBottom: 24 }}>
                  <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleUpdateProfile}
                  >
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="username"
                          label="用户名"
                          rules={[{ required: true, message: '请输入用户名' }]}
                        >
                          <Input prefix={<UserOutlined />} placeholder="用户名" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="email"
                          label="邮箱"
                          rules={[
                            { required: true, message: '请输入邮箱' },
                            { type: 'email', message: '请输入有效的邮箱地址' }
                          ]}
                        >
                          <Input prefix={<MailOutlined />} placeholder="邮箱" />
                        </Form.Item>
                      </Col>
                    </Row>
                    
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="phone"
                          label="手机号"
                          rules={[{ required: true, message: '请输入手机号' }]}
                        >
                          <Input prefix={<PhoneOutlined />} placeholder="手机号" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="department"
                          label="部门"
                        >
                          <Input prefix={<TeamOutlined />} placeholder="部门" />
                        </Form.Item>
                      </Col>
                    </Row>
                    
                    <Form.Item>
                      <Button 
                        type="primary" 
                        htmlType="submit" 
                        icon={<SaveOutlined />}
                        loading={saving}
                      >
                        保存修改
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>
              </TabPane>
              
              <TabPane tab="修改密码" key="password">
                <Card title="修改密码">
                  <Form
                    form={passwordForm}
                    layout="vertical"
                    onFinish={handleChangePassword}
                  >
                    <Form.Item
                      name="oldPassword"
                      label="当前密码"
                      rules={[{ required: true, message: '请输入当前密码' }]}
                    >
                      <Input.Password prefix={<LockOutlined />} placeholder="当前密码" />
                    </Form.Item>
                    
                    <Form.Item
                      name="newPassword"
                      label="新密码"
                      rules={[
                        { required: true, message: '请输入新密码' },
                        { min: 6, message: '密码长度不能少于6个字符' }
                      ]}
                    >
                      <Input.Password prefix={<LockOutlined />} placeholder="新密码" />
                    </Form.Item>
                    
                    <Form.Item
                      name="confirmPassword"
                      label="确认新密码"
                      dependencies={['newPassword']}
                      rules={[
                        { required: true, message: '请确认新密码' },
                        ({ getFieldValue }) => ({
                          validator(_, value) {
                            if (!value || getFieldValue('newPassword') === value) {
                              return Promise.resolve();
                            }
                            return Promise.reject(new Error('两次输入的密码不一致'));
                          },
                        }),
                      ]}
                    >
                      <Input.Password prefix={<LockOutlined />} placeholder="确认新密码" />
                    </Form.Item>
                    
                    <Form.Item>
                      <Button 
                        type="primary" 
                        htmlType="submit" 
                        icon={<SaveOutlined />}
                        loading={saving}
                      >
                        修改密码
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>
              </TabPane>
            </Tabs>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default UserProfile;
