import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Progress, Spin, Typography, Tabs, Alert, Divider, Tag } from 'antd';
import { 
  ClusterOutlined, 
  DesktopOutlined, 
  DatabaseOutlined, 
  RocketOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const ClusterResourceInfo = () => {
  const [clusters, setClusters] = useState([]);
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 获取所有集群信息
  const fetchClusters = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/clusters');
      if (response.data.status === 'success') {
        setClusters(response.data.data);
        // 如果有集群数据，默认选择第一个
        if (response.data.data.length > 0) {
          fetchClusterDetail(response.data.data[0].id);
        } else {
          setLoading(false);
        }
      } else {
        setError('获取集群列表失败');
        setLoading(false);
      }
    } catch (err) {
      setError('获取集群列表时发生错误: ' + err.message);
      setLoading(false);
    }
  };

  // 获取特定集群的详细信息
  const fetchClusterDetail = async (clusterId) => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/clusters/${clusterId}`);
      if (response.data.status === 'success') {
        setSelectedCluster(response.data.data);
      } else {
        setError('获取集群详情失败');
      }
      setLoading(false);
    } catch (err) {
      setError('获取集群详情时发生错误: ' + err.message);
      setLoading(false);
    }
  };

  // 初始化时获取集群列表
  useEffect(() => {
    fetchClusters();
    
    // 设置定时刷新（每30秒刷新一次）
    const intervalId = setInterval(() => {
      if (selectedCluster) {
        fetchClusterDetail(selectedCluster.id);
      } else {
        fetchClusters();
      }
    }, 30000);

    // 组件卸载时清除定时器
    return () => clearInterval(intervalId);
  }, []);

  // 切换选中的集群
  const handleClusterChange = (clusterId) => {
    fetchClusterDetail(clusterId);
  };

  // 格式化内存大小显示
  const formatMemory = (memoryMB) => {
    if (memoryMB >= 1024) {
      return `${(memoryMB / 1024).toFixed(2)} GB`;
    }
    return `${memoryMB} MB`;
  };

  // 计算内存使用率
  const calculateMemoryUsage = (total, available) => {
    if (!total || !available) return 0;
    const used = total - available;
    return Math.round((used / total) * 100);
  };

  // 渲染集群概览卡片
  const renderClusterOverview = () => {
    if (!selectedCluster) return null;

    const totalNodes = selectedCluster.nodes.length;
    const totalGPUs = selectedCluster.nodes.reduce((acc, node) => acc + node.gpus.length, 0);
    const totalCPUCores = selectedCluster.nodes.reduce((acc, node) => {
      return acc + (node.cpu_info?.cores || 0);
    }, 0);
    const totalMemory = selectedCluster.nodes.reduce((acc, node) => {
      return acc + (node.memory_total || 0);
    }, 0);

    return (
      <Card title={
        <span>
          <ClusterOutlined /> 集群概览: {selectedCluster.name}
        </span>
      } bordered={false}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic 
              title="节点数量" 
              value={totalNodes} 
              prefix={<DesktopOutlined />} 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="GPU总数" 
              value={totalGPUs} 
              prefix={<RocketOutlined />} 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="CPU核心总数" 
              value={totalCPUCores} 
              prefix={<BarChartOutlined />} 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="内存总量" 
              value={formatMemory(totalMemory)} 
              prefix={<DatabaseOutlined />} 
            />
          </Col>
        </Row>
      </Card>
    );
  };

  // 渲染节点详情表格
  const renderNodeDetails = () => {
    if (!selectedCluster) return null;

    const columns = [
      {
        title: '节点名称',
        dataIndex: 'name',
        key: 'name',
        render: (text, record) => (
          <span>
            {text} 
            <Tag color={record.status === 'online' ? 'green' : 'red'} style={{ marginLeft: 8 }}>
              {record.status === 'online' ? '在线' : '离线'}
            </Tag>
          </span>
        )
      },
      {
        title: 'IP地址',
        dataIndex: 'ip',
        key: 'ip',
      },
      {
        title: 'CPU',
        dataIndex: 'cpu_info',
        key: 'cpu',
        render: (cpu_info) => (
          <div>
            <div>{cpu_info?.model || '未知'}</div>
            <div>{cpu_info?.cores || 0} 核心 / {cpu_info?.architecture || '未知'}</div>
          </div>
        )
      },
      {
        title: '内存',
        key: 'memory',
        render: (text, record) => {
          const memoryUsage = calculateMemoryUsage(record.memory_total, record.memory_available);
          return (
            <div>
              <div>{formatMemory(record.memory_total || 0)}</div>
              <Progress 
                percent={memoryUsage} 
                size="small" 
                status={memoryUsage > 80 ? "exception" : "normal"}
              />
            </div>
          );
        }
      },
      {
        title: 'GPU数量',
        dataIndex: 'gpus',
        key: 'gpus',
        render: (gpus) => gpus.length
      },
      {
        title: '状态',
        key: 'status',
        render: (text, record) => (
          <span>
            {record.status === 'online' ? 
              <CheckCircleOutlined style={{ color: 'green' }} /> : 
              <CloseCircleOutlined style={{ color: 'red' }} />
            }
            {' '}
            {record.status === 'online' ? '在线' : '离线'}
          </span>
        )
      }
    ];

    return (
      <Card title={<span><DesktopOutlined /> 节点详情</span>} bordered={false} style={{ marginTop: 16 }}>
        <Table 
          dataSource={selectedCluster.nodes} 
          columns={columns} 
          rowKey="id"
          expandable={{
            expandedRowRender: record => <GPUDetails gpus={record.gpus} />,
          }}
        />
      </Card>
    );
  };

  // 渲染GPU详情
  const GPUDetails = ({ gpus }) => {
    const columns = [
      {
        title: 'GPU名称',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: '类型',
        dataIndex: 'gpu_type',
        key: 'type',
        render: (text) => <Tag color="blue">{text}</Tag>
      },
      {
        title: '显存',
        dataIndex: 'memory_total',
        key: 'memory',
        render: (memory) => formatMemory(memory)
      },
      {
        title: '计算能力',
        dataIndex: 'compute_capability',
        key: 'compute_capability',
        render: (text) => text || '未知'
      },
      {
        title: '驱动版本',
        key: 'driver_version',
        render: (text, record) => record.extra_info?.driver_version || '未知'
      }
    ];

    return (
      <div style={{ margin: '0 16px' }}>
        <Divider orientation="left">GPU资源</Divider>
        <Table 
          columns={columns} 
          dataSource={gpus} 
          rowKey="id" 
          pagination={false}
          size="small"
        />
      </div>
    );
  };

  // 渲染集群选择标签页
  const renderClusterTabs = () => {
    return (
      <Tabs 
        activeKey={selectedCluster?.id} 
        onChange={handleClusterChange}
        type="card"
        style={{ marginBottom: 16 }}
      >
        {clusters.map(cluster => (
          <TabPane 
            tab={
              <span>
                {cluster.adapter_type === 'nvidia' ? <RocketOutlined /> : <DesktopOutlined />}
                {' '}
                {cluster.name}
                {' '}
                <Tag color={cluster.status === 'online' ? 'green' : 'red'}>
                  {cluster.status === 'online' ? '在线' : '离线'}
                </Tag>
              </span>
            } 
            key={cluster.id}
          />
        ))}
      </Tabs>
    );
  };

  return (
    <div className="cluster-resource-info">
      <Title level={2}>集群资源信息</Title>
      <Text type="secondary" style={{ marginBottom: 16, display: 'block' }}>
        查看集群的计算资源信息，包括CPU、内存、GPU等硬件资源的使用情况
      </Text>

      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          closable
          style={{ marginBottom: 16 }}
          onClose={() => setError(null)}
        />
      )}

      {loading && !selectedCluster ? (
        <div style={{ textAlign: 'center', margin: '50px 0' }}>
          <Spin size="large" tip="加载集群信息..." />
        </div>
      ) : (
        <>
          {clusters.length === 0 ? (
            <Alert
              message="未找到集群"
              description="当前没有注册的集群。请先注册一个集群。"
              type="info"
              showIcon
            />
          ) : (
            <>
              {renderClusterTabs()}
              {renderClusterOverview()}
              {renderNodeDetails()}
            </>
          )}
        </>
      )}
    </div>
  );
};

export default ClusterResourceInfo;
