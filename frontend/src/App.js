import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import './App.css';

// 导入组件
import Navigation from './components/Navigation';
import ModelDeployForm from './components/ModelDeployForm';
import UserManagement from './components/UserManagement';
import ModelList from './components/ModelList';
import Dashboard from './components/Dashboard';
import ModelConfig from './components/ModelConfig';
import ModelChat from './components/ModelChat';
import ImageManagement from './components/ImageManagement';
import Login from './components/Login';
import UserProfile from './components/UserProfile';
import ApiKeyManagement from './components/ApiKeyManagement';
import ClusterRegistration from './components/ClusterRegistration';
import ClusterList from './components/ClusterList';

const { Content, Footer } = Layout;

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // 从 localStorage 中获取用户信息
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('解析用户信息失败:', error);
      }
    }
  }, []);

  // 登录成功回调
  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  // 登出回调
  const handleLogout = () => {
    setUser(null);
  };

  // 需要登录才能访问的路由
  const ProtectedRoute = ({ children }) => {
    if (!localStorage.getItem('user')) {
      return <Navigate to="/login" replace />;
    }
    return children;
  };

  return (
    <Router>
      <Layout className="layout" style={{ minHeight: '100vh' }}>
        <Navigation />
        <Content style={{ padding: '0 50px', marginTop: 64 }}>
          <div className="site-layout-content" style={{ padding: 24, minHeight: 380 }}>
            <Routes>
              <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} />} />
              <Route path="/" element={
                <ProtectedRoute>
                  <ModelDeployForm />
                </ProtectedRoute>
              } />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
              <Route path="/models" element={
                <ProtectedRoute>
                  <ModelList />
                </ProtectedRoute>
              } />
              <Route path="/model-configs" element={
                <ProtectedRoute>
                  <ModelConfig />
                </ProtectedRoute>
              } />
              <Route path="/model-chat" element={
                <ProtectedRoute>
                  <ModelChat />
                </ProtectedRoute>
              } />
              <Route path="/users" element={
                <ProtectedRoute>
                  <UserManagement />
                </ProtectedRoute>
              } />
              <Route path="/images" element={
                <ProtectedRoute>
                  <ImageManagement />
                </ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute>
                  <UserProfile />
                </ProtectedRoute>
              } />
              <Route path="/api-keys" element={
                <ProtectedRoute>
                  <ApiKeyManagement />
                </ProtectedRoute>
              } />
              <Route path="/clusters" element={
                <ProtectedRoute>
                  <ClusterList />
                </ProtectedRoute>
              } />
              <Route path="/register-cluster" element={
                <ProtectedRoute>
                  <ClusterRegistration />
                </ProtectedRoute>
              } />
              <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          大模型部署平台 ©{new Date().getFullYear()} by 后端团队
        </Footer>
      </Layout>
    </Router>
  );
}

export default App;
