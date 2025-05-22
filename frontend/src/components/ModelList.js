import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Input, Space, Tag, Modal, 
  Card, Descriptions, Checkbox, Row, Col, message 
} from 'antd';
import { 
  SearchOutlined, 
  StopOutlined, 
  PlayCircleOutlined, 
  InfoCircleOutlined 
} from '@ant-design/icons';

const ModelList = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 5,
    total: 0
  });
  const [searchText, setSearchText] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentModel, setCurrentModel] = useState(null);

  // 获取模型列表
  const fetchModels = async (page = 1, pageSize = 5, search = '') => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/api/models?page=${page}&pageSize=${pageSize}&search=${search}`
      );
      const result = await response.json();
      
      if (result.status === 'success') {
        setModels(result.data.models);
        setPagination({
          current: result.data.pagination.current,
          pageSize: result.data.pagination.pageSize,
          total: result.data.pagination.total
        });
      } else {
        message.error('获取模型列表失败');
      }
    } catch (error) {
      message.error('获取模型列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels(pagination.current, pagination.pageSize, searchText);
  }, []);

  // 处理表格变化（分页、筛选、排序）
  const handleTableChange = (pagination) => {
    fetchModels(pagination.current, pagination.pageSize, searchText);
  };

  // 处理搜索
  const handleSearch = () => {
    fetchModels(1, pagination.pageSize, searchText);
  };

  // 处理搜索框按键事件
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // 处理查看详情
  const handleViewDetails = (model) => {
    setCurrentModel(model);
    setDetailVisible(true);
  };

  // 处理状态变更
  const handleStatusChange = async (modelId, newStatus) => {
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/models/${modelId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        message.success(`模型${newStatus === 'running' ? '启动' : '停止'}成功`);
        // 更新本地数据
        setModels(models.map(model => 
          model.id === modelId ? { ...model, status: newStatus } : model
        ));
      } else {
        message.error(result.message || '操作失败');
      }
    } catch (error) {
      message.error('操作失败: ' + error.message);
    }
  };

  // 批量操作
  const handleBatchOperation = (operation) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择模型');
      return;
    }

    Modal.confirm({
      title: `确定要${operation === 'start' ? '启动' : '停止'}选中的模型吗？`,
      content: `将${operation === 'start' ? '启动' : '停止'}${selectedRowKeys.length}个模型`,
      onOk: async () => {
        const newStatus = operation === 'start' ? 'running' : 'stopped';
        const promises = selectedRowKeys.map(modelId => 
          handleStatusChange(modelId, newStatus)
        );
        
        try {
          await Promise.all(promises);
          message.success(`批量${operation === 'start' ? '启动' : '停止'}成功`);
          fetchModels(pagination.current, pagination.pageSize, searchText);
          setSelectedRowKeys([]);
        } catch (error) {
          message.error('批量操作失败');
        }
      }
    });
  };

  // 表格列定义
  const columns = [
    {
      title: '模型标识',
      dataIndex: 'modelId',
      key: 'modelId',
      width: 160,
    },
    {
      title: '模型名称',
      dataIndex: 'modelName',
      key: 'modelName',
      render: (text) => <span style={{ fontWeight: 'bold' }}>{text}</span>,
      width: 160,
    },
    {
      title: '部署方法',
      dataIndex: 'backend',
      key: 'backend',
      width: 100,
    },
    {
      title: '服务器',
      dataIndex: 'server',
      key: 'server',
      width: 120,
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 80,
    },
    {
      title: 'GPU',
      dataIndex: 'gpu',
      key: 'gpu',
      width: 80,
    },
    {
      title: '集群',
      dataIndex: 'cluster',
      key: 'cluster',
      width: 160,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status) => (
        <Tag color={status === 'running' ? 'green' : 'red'}>
          {status === 'running' ? '运行中' : '已停止'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space size="middle">
          {record.status === 'running' ? (
            <Button 
              icon={<StopOutlined />} 
              danger
              size="small"
              onClick={() => handleStatusChange(record.id, 'stopped')}
            >
              停止
            </Button>
          ) : (
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />}
              size="small"
              onClick={() => handleStatusChange(record.id, 'running')}
            >
              启动
            </Button>
          )}
          <Button 
            type="default" 
            icon={<InfoCircleOutlined />}
            size="small"
            onClick={() => handleViewDetails(record)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ];

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
  };

  return (
    <div className="model-list-container">
      <Card title="模型实例列表" style={{ width: '100%' }}>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Input
              placeholder="搜索模型名称、后端、服务器或GPU"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onKeyPress={handleKeyPress}
              suffix={
                <SearchOutlined 
                  style={{ cursor: 'pointer' }} 
                  onClick={handleSearch}
                />
              }
            />
          </Col>
          <Col span={16} style={{ textAlign: 'right' }}>
            <Space>
              <Button 
                type="primary" 
                onClick={() => handleBatchOperation('start')}
                disabled={selectedRowKeys.length === 0}
              >
                批量启动
              </Button>
              <Button 
                danger 
                onClick={() => handleBatchOperation('stop')}
                disabled={selectedRowKeys.length === 0}
              >
                批量停止
              </Button>
            </Space>
          </Col>
        </Row>
        
        <Table 
          rowSelection={rowSelection}
          columns={columns} 
          dataSource={models} 
          rowKey="id" 
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
        />
      </Card>

      {/* 模型详情弹窗 */}
      <Modal
        title="模型详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {currentModel && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="模型ID" span={2}>{currentModel.id}</Descriptions.Item>
            <Descriptions.Item label="模型标识" span={2}>{currentModel.modelId}</Descriptions.Item>
            <Descriptions.Item label="模型名称" span={2}>{currentModel.modelName}</Descriptions.Item>
            <Descriptions.Item label="部署方法">{currentModel.backend}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={currentModel.status === 'running' ? 'green' : 'red'}>
                {currentModel.status === 'running' ? '运行中' : '已停止'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="服务器">{currentModel.server}</Descriptions.Item>
            <Descriptions.Item label="端口">{currentModel.port}</Descriptions.Item>
            <Descriptions.Item label="GPU">{currentModel.gpu}</Descriptions.Item>
            <Descriptions.Item label="集群">{currentModel.cluster}</Descriptions.Item>
            <Descriptions.Item label="模型路径" span={2}>
              <span style={{ wordBreak: 'break-all' }}>{currentModel.modelPath}</span>
            </Descriptions.Item>
            <Descriptions.Item label="API端点" span={2}>
              {`http://${currentModel.server}:${currentModel.port}/api/predict`}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default ModelList;
