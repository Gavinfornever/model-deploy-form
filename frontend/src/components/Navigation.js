import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Layout, Menu, Row, Col } from 'antd';
import { 
  UserOutlined, DeploymentUnitOutlined, AppstoreOutlined, 
  DashboardOutlined, SettingOutlined, CommentOutlined, 
  CloudOutlined, KeyOutlined, ClusterOutlined 
} from '@ant-design/icons';
import UserAvatar from './UserAvatar';

const { Header } = Layout;

const Navigation = () => {
  const location = useLocation();
  const [current, setCurrent] = useState(location.pathname);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // 检查用户是否已登录
    const user = localStorage.getItem('user');
    setIsLoggedIn(!!user);
  }, []);

  const handleClick = (e) => {
    setCurrent(e.key);
  };
  
  const handleLogout = () => {
    setIsLoggedIn(false);
  };

  return (
    <Header style={{ background: '#2366a8', padding: '0 24px' }}>
      <Row justify="space-between" align="middle">
        <Col>
          <div className="logo" style={{ color: 'white', fontSize: '18px', fontWeight: 'bold', lineHeight: '64px' }}>
            大模型部署平台
          </div>
        </Col>
        <Col flex="auto">
          <Menu
            theme="dark"
            mode="horizontal"
            onClick={handleClick}
            selectedKeys={[current]}
            style={{ background: '#2366a8', lineHeight: '64px', border: 'none' }}
        items={[
          {
            key: '/clusters',
            icon: <ClusterOutlined />,
            label: <Link to="/clusters">集群管理</Link>,
          },
          {
            key: '/',
            icon: <DeploymentUnitOutlined />,
            label: <Link to="/">模型部署</Link>,
          },
          {
            key: '/model-configs',
            icon: <SettingOutlined />,
            label: <Link to="/model-configs">模型配置</Link>,
          },
          {
            key: '/images',
            icon: <CloudOutlined />,
            label: <Link to="/images">镜像管理</Link>,
          },
          {
            key: '/models',
            icon: <AppstoreOutlined />,
            label: <Link to="/models">实例列表</Link>,
          },
          {
            key: '/api-keys',
            icon: <KeyOutlined />,
            label: <Link to="/api-keys">API密钥管理</Link>,
          },
          {
            key: '/users',
            icon: <UserOutlined />,
            label: <Link to="/users">用户管理</Link>,
          },
          {
            key: '/model-chat',
            icon: <CommentOutlined />,
            label: <Link to="/model-chat">模型对话</Link>,
          },
          {
            key: '/dashboard',
            icon: <DashboardOutlined />,
            label: <Link to="/dashboard">仪表盘</Link>,
          }
        ]}
      />
        </Col>
        <Col>
          <div style={{ display: 'flex', alignItems: 'center', height: '64px' }}>
            <UserAvatar onLogout={handleLogout} />
          </div>
        </Col>
      </Row>
    </Header>
  );
};

export default Navigation;
