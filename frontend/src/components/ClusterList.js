import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Button, Space, Tag, Tooltip, 
  Modal, Statistic, Row, Col, Typography, Spin, 
  Descriptions, Divider, Progress, Badge
} from 'antd';
import { 
  CloudServerOutlined, PlusOutlined, ReloadOutlined, 
  InfoCircleOutlined, DeleteOutlined, DesktopOutlined,
  CheckCircleOutlined, CloseCircleOutlined, SyncOutlined
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;

const ClusterList = () => {
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [clusterDetail, setClusterDetail] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  // 获取集群列表
  const fetchClusters = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5000/api/clusters', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.status === 'success') {
        setClusters(response.data.data);
      } else {
        console.error('获取集群列表失败:', response.data.message);
      }
    } catch (error) {
      console.error('获取集群列表错误:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取集群详情
  const fetchClusterDetail = async (clusterId) => {
    setDetailLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`http://localhost:5000/api/clusters/${clusterId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.status === 'success') {
        setClusterDetail(response.data.data);
        setDetailModalVisible(true);
      } else {
        console.error('获取集群详情失败:', response.data.message);
      }
    } catch (error) {
      console.error('获取集群详情错误:', error);
    } finally {
      setDetailLoading(false);
    }
  };

  // 删除集群
  const deleteCluster = async (clusterId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(`http://localhost:5000/api/clusters/${clusterId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.status === 'success') {
        fetchClusters();
      } else {
        console.error('删除集群失败:', response.data.message);
      }
    } catch (error) {
      console.error('删除集群错误:', error);
    }
  };

  // 首次加载时获取集群列表
  useEffect(() => {
    fetchClusters();
  }, []);

  // 集群列表表格列定义
  const columns = [
    {
      title: '集群名称',
      dataIndex: 'name',
      key: 'name',
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: '类型',
      dataIndex: 'adapter_type',
      key: 'adapter_type',
      render: (type) => {
        let color = 'blue';
        let text = type;
        
        if (type === 'apple') {
          color = 'geekblue';
          text = 'Apple Silicon';
        } else if (type === 'nvidia') {
          color = 'green';
          text = 'NVIDIA';
        }
        
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        if (status === 'online') {
          return <Badge status="success" text="在线" />;
        } else if (status === 'offline') {
          return <Badge status="error" text="离线" />;
        } else {
          return <Badge status="processing" text="连接中" />;
        }
      },
    },
    {
      title: '节点数',
      dataIndex: 'nodes_count',
      key: 'nodes_count',
    },
    {
      title: 'GPU数',
      dataIndex: 'gpus_count',
      key: 'gpus_count',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button 
              type="text" 
              icon={<InfoCircleOutlined />} 
              onClick={() => fetchClusterDetail(record.id)}
            />
          </Tooltip>
          <Tooltip title="删除集群">
            <Button 
              type="text" 
              danger 
              icon={<DeleteOutlined />} 
              onClick={() => {
                Modal.confirm({
                  title: '确认删除',
                  content: `确定要删除集群 "${record.name}" 吗？此操作不可恢复。`,
                  onOk: () => deleteCluster(record.id)
                });
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 渲染集群详情模态框
  const renderDetailModal = () => {
    if (!clusterDetail) return null;

    const nodes = clusterDetail.nodes || [];
    const totalGpus = nodes.reduce((sum, node) => sum + (node.gpus ? node.gpus.length : 0), 0);

    return (
      <Modal
        title={`集群详情: ${clusterDetail.name}`}
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        <Spin spinning={detailLoading}>
          {/* 集群概览 */}
          <Row gutter={16}>
            <Col span={8}>
              <Statistic 
                title="节点数量" 
                value={nodes.length} 
                prefix={<DesktopOutlined />} 
              />
            </Col>
            <Col span={8}>
              <Statistic 
                title="GPU总数" 
                value={totalGpus} 
                prefix={<CloudServerOutlined />} 
              />
            </Col>
            <Col span={8}>
              <Statistic 
                title="状态" 
                value={clusterDetail.status === 'online' ? '在线' : '离线'} 
                valueStyle={{ color: clusterDetail.status === 'online' ? '#52c41a' : '#ff4d4f' }}
                prefix={clusterDetail.status === 'online' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              />
            </Col>
          </Row>

          <Divider />

          {/* 集群信息 */}
          <Descriptions title="集群信息" bordered>
            <Descriptions.Item label="集群ID" span={3}>{clusterDetail.id}</Descriptions.Item>
            <Descriptions.Item label="适配器类型" span={3}>
              {clusterDetail.adapter_type === 'apple' ? 'Apple Silicon' : 'NVIDIA'}
            </Descriptions.Item>
          </Descriptions>

          <Divider />

          {/* 节点列表 */}
          <Title level={4}>节点列表</Title>
          {nodes.length === 0 ? (
            <Text type="secondary">暂无节点信息</Text>
          ) : (
            nodes.map((node, index) => (
              <Card 
                key={node.id} 
                title={`节点: ${node.name}`}
                style={{ marginBottom: 16 }}
                type="inner"
                extra={
                  <Tag color={node.status === 'online' ? 'green' : 'red'}>
                    {node.status === 'online' ? '在线' : '离线'}
                  </Tag>
                }
              >
                <Descriptions size="small" column={2}>
                  <Descriptions.Item label="节点ID">{node.id}</Descriptions.Item>
                  <Descriptions.Item label="IP地址">{node.ip}</Descriptions.Item>
                  {node.metadata && (
                    <>
                      <Descriptions.Item label="操作系统">
                        {node.metadata.os} {node.metadata.os_version}
                      </Descriptions.Item>
                      <Descriptions.Item label="主机名">
                        {node.metadata.hostname}
                      </Descriptions.Item>
                      {node.metadata.cpu_cores && (
                        <Descriptions.Item label="CPU核心数">
                          {node.metadata.cpu_cores}
                        </Descriptions.Item>
                      )}
                      {node.metadata.cpu_model && (
                        <Descriptions.Item label="CPU型号">
                          {node.metadata.cpu_model}
                        </Descriptions.Item>
                      )}
                      {node.metadata.memory_total && (
                        <Descriptions.Item label="内存大小">
                          {(node.metadata.memory_total / 1024).toFixed(2)} GB
                        </Descriptions.Item>
                      )}
                    </>
                  )}
                </Descriptions>

                {/* GPU列表 */}
                {node.gpus && node.gpus.length > 0 && (
                  <>
                    <Divider orientation="left">GPU ({node.gpus.length})</Divider>
                    <Table
                      dataSource={node.gpus}
                      rowKey="id"
                      size="small"
                      pagination={false}
                      columns={[
                        {
                          title: 'GPU名称',
                          dataIndex: 'name',
                          key: 'name',
                        },
                        {
                          title: '类型',
                          dataIndex: 'gpu_type',
                          key: 'gpu_type',
                          render: (type) => (
                            <Tag color={type === 'apple' ? 'geekblue' : 'green'}>
                              {type}
                            </Tag>
                          )
                        },
                        {
                          title: '显存',
                          dataIndex: 'memory_total',
                          key: 'memory_total',
                          render: (memory) => `${(memory / 1024).toFixed(2)} GB`
                        }
                      ]}
                    />
                  </>
                )}
              </Card>
            ))
          )}
        </Spin>
      </Modal>
    );
  };

  return (
    <div className="cluster-list">
      <Card
        title={
          <Space>
            <CloudServerOutlined />
            <span>计算集群</span>
          </Space>
        }
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={fetchClusters}
              loading={loading}
            >
              刷新
            </Button>
            <Link to="/register-cluster">
              <Button type="primary" icon={<PlusOutlined />}>
                注册新集群
              </Button>
            </Link>
          </Space>
        }
      >
        <Table
          dataSource={clusters}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无集群，请点击"注册新集群"按钮添加' }}
        />
      </Card>

      {renderDetailModal()}
    </div>
  );
};

export default ClusterList;
