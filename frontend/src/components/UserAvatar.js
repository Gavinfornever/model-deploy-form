import React, { useState, useEffect } from 'react';
import { Avatar, Dropdown, Menu, message } from 'antd';
import { 
  UserOutlined, SettingOutlined, LogoutOutlined, 
  KeyOutlined, ProfileOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const UserAvatar = ({ onLogout }) => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // 从localStorage获取用户信息
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
      } catch (error) {
        console.error('解析用户信息失败:', error);
      }
    }
  }, []);

  // 处理登出
  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    
    if (onLogout) {
      onLogout();
    }
    
    message.success('已成功退出登录');
    navigate('/login');
  };

  // 如果没有用户信息，显示登录按钮
  if (!user) {
    return (
      <div 
        style={{ cursor: 'pointer' }}
        onClick={() => navigate('/login')}
      >
        <Avatar icon={<UserOutlined />} />
        <span style={{ marginLeft: 8, color: '#fff' }}>登录</span>
      </div>
    );
  }

  // 用户菜单
  const menu = (
    <Menu>
      <Menu.Item key="profile" icon={<ProfileOutlined />} onClick={() => navigate('/profile')}>
        个人信息
      </Menu.Item>
      <Menu.Item key="settings" icon={<SettingOutlined />} onClick={() => navigate('/settings')}>
        账号设置
      </Menu.Item>
      <Menu.Item key="password" icon={<KeyOutlined />} onClick={() => navigate('/profile?tab=password')}>
        修改密码
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={handleLogout}>
        退出登录
      </Menu.Item>
    </Menu>
  );

  return (
    <Dropdown overlay={menu} trigger={['click']}>
      <div style={{ cursor: 'pointer' }}>
        <Avatar src={user.avatar} icon={!user.avatar && <UserOutlined />} />
        <span style={{ marginLeft: 8, color: '#fff' }}>{user.username}</span>
      </div>
    </Dropdown>
  );
};

export default UserAvatar;
