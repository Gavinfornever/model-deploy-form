import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Space, Select, message, Popconfirm, Tabs, Tag, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined, EyeInvisibleOutlined, LockOutlined, UserOutlined, MailOutlined, PhoneOutlined, TeamOutlined, CalendarOutlined } from '@ant-design/icons';
import moment from 'moment';

const { Option } = Select;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [editingUser, setEditingUser] = useState(null);

  // 获取用户列表
  const fetchUsers = async () => {
    setLoading(true);
    try {
      // 使用带有认证的请求
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const response = await fetch('http://127.0.0.1:5000/api/users', {
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        }
      });
      const result = await response.json();
      if (result.status === 'success') {
        setUsers(result.data);
      } else {
        message.error('获取用户列表失败');
      }
    } catch (error) {
      message.error('获取用户列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 180,
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      width: 150,
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 120,
      render: (role) => {
        let color = 'blue';
        if (role === '管理员') color = 'red';
        else if (role === '模型管理员') color = 'orange';
        else if (role === '访客') color = 'green';
        return <Tag color={color}>{role}</Tag>;
      },
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        return status === 'active' ? 
          <Tag color="green">正常</Tag> : 
          <Tag color="red">禁用</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      key: 'createTime',
      width: 180,
      render: (time) => moment(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '最后登录',
      dataIndex: 'lastLogin',
      key: 'lastLogin',
      width: 180,
      render: (time) => time ? moment(time).format('YYYY-MM-DD HH:mm:ss') : '从未登录',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此用户吗?"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              danger 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 打开编辑模态框
  const handleEdit = (user) => {
    setEditingUser(user);
    form.setFieldsValue({
      ...user,
      // 不填充密码字段，如果不修改则保持原密码
      password: '',
      confirmPassword: ''
    });
    setModalVisible(true);
  };

  // 打开新增模态框
  const handleAdd = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 删除用户
  const handleDelete = async (userId) => {
    try {
      // 使用带有认证的请求
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const response = await fetch(`http://127.0.0.1:5000/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        }
      });
      const result = await response.json();
      if (result.status === 'success') {
        message.success('用户删除成功');
        fetchUsers();
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
      
      // 处理密码字段
      const userData = { ...values };
      
      // 如果是编辑用户且没有输入密码，则不发送密码字段
      if (editingUser && (!values.password || values.password.trim() === '')) {
        delete userData.password;
        delete userData.confirmPassword;
      }
      
      // 始终删除确认密码字段，因为后端不需要
      delete userData.confirmPassword;
      
      // 添加创建时间和状态
      if (!editingUser) {
        userData.createTime = new Date().toISOString();
        userData.status = 'active';
      }
      
      const url = editingUser 
        ? `http://127.0.0.1:5000/api/users/${editingUser.id}`
        : 'http://127.0.0.1:5000/api/users';
      
      const method = editingUser ? 'PUT' : 'POST';
      
      // 使用带有认证的请求
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const response = await fetch(url, {
        method,
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        message.success(`${editingUser ? '更新' : '创建'}用户成功`);
        setModalVisible(false);
        fetchUsers();
      } else {
        message.error(result.message || `${editingUser ? '更新' : '创建'}失败`);
      }
    } catch (error) {
      message.error(`${editingUser ? '更新' : '创建'}失败: ` + error.message);
    }
  };

  return (
    <div className="user-management">
      <div className="header-actions" style={{ marginBottom: 16 }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleAdd}
        >
          添加用户
        </Button>
      </div>
      
      <Table 
        columns={columns} 
        dataSource={users} 
        rowKey="id" 
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
      
      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText={editingUser ? '更新' : '创建'}
        cancelText="取消"
        width={700}
      >
        <Tabs defaultActiveKey="basic">
          <Tabs.TabPane tab="基本信息" key="basic">
            <Form
              form={form}
              layout="vertical"
            >
              <Form.Item
                name="username"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="请输入用户名" />
              </Form.Item>
              
              {/* 新增密码字段 */}
              <Form.Item
                name="password"
                label={editingUser ? '密码（留空不修改）' : '密码'}
                rules={[{ 
                  required: !editingUser, 
                  message: '请输入密码' 
                },
                { 
                  min: 6, 
                  message: '密码长度不能少于6个字符' 
                }]}
              >
                <Input.Password 
                  prefix={<LockOutlined />} 
                  placeholder={editingUser ? '留空不修改密码' : '请输入密码'} 
                />
              </Form.Item>
              
              {/* 新增确认密码字段 */}
              <Form.Item
                name="confirmPassword"
                label={editingUser ? '确认密码（留空不修改）' : '确认密码'}
                dependencies={['password']}
                rules={[
                  {
                    required: !editingUser,
                    message: '请确认密码',
                  },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value && !getFieldValue('password')) {
                        return Promise.resolve();
                      }
                      if (!value || getFieldValue('password') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('两次输入的密码不一致'));
                    },
                  }),
                ]}
              >
                <Input.Password 
                  prefix={<LockOutlined />} 
                  placeholder={editingUser ? '留空不修改密码' : '请再次输入密码'} 
                />
              </Form.Item>
              
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input prefix={<MailOutlined />} placeholder="请输入邮箱" />
              </Form.Item>
              
              <Form.Item
                name="phone"
                label="手机号"
                rules={[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }
                ]}
              >
                <Input prefix={<PhoneOutlined />} placeholder="请输入手机号" />
              </Form.Item>
            </Form>
          </Tabs.TabPane>
          
          <Tabs.TabPane tab="角色与权限" key="role">
            <Form
              form={form}
              layout="vertical"
            >
              <Form.Item
                name="role"
                label="角色"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select placeholder="请选择角色">
                  <Option value="管理员">管理员</Option>
                  <Option value="模型管理员">模型管理员</Option>
                  <Option value="普通用户">普通用户</Option>
                  <Option value="访客">访客</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="department"
                label="部门"
                rules={[{ required: true, message: '请输入部门' }]}
              >
                <Input prefix={<TeamOutlined />} placeholder="请输入部门" />
              </Form.Item>
              
              <Form.Item
                name="status"
                label="账号状态"
                initialValue="active"
              >
                <Select placeholder="请选择账号状态">
                  <Option value="active">正常</Option>
                  <Option value="disabled">禁用</Option>
                </Select>
              </Form.Item>
            </Form>
          </Tabs.TabPane>
        </Tabs>
      </Modal>
    </div>
  );
};

export default UserManagement;
