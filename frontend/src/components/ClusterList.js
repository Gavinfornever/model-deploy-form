import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Button, Space, Tag, Tooltip, 
  Modal, Statistic, Row, Col, Typography, Spin, 
  Descriptions, Divider, Progress, Badge, Tabs, Empty,
  Tree, List
} from 'antd';
import { 
  CloudServerOutlined, PlusOutlined, ReloadOutlined, 
  InfoCircleOutlined, DeleteOutlined, DesktopOutlined,
  CheckCircleOutlined, CloseCircleOutlined, SyncOutlined,
  DatabaseOutlined, BarChartOutlined, RocketOutlined
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
      const response = await axios.get('http://localhost:5001/api/clusters');

      if (response.data.status === 'success') {
        const clusterList = response.data.data;
        setClusters(clusterList);
        
        // 自动获取每个集群的详细信息
        for (const cluster of clusterList) {
          fetchClusterDetail(cluster.id, false);
        }
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
  const fetchClusterDetail = async (clusterId, showModal = true) => {
    if (showModal) {
      setDetailLoading(true);
    }
    try {
      const response = await axios.get(`http://localhost:5001/api/clusters/${clusterId}`);

      if (response.data.status === 'success') {
        const detailData = response.data.data;
        setClusterDetail(detailData);
        
        // 更新集群列表中的节点信息
        setClusters(prevClusters => {
          return prevClusters.map(cluster => {
            if (cluster.id === clusterId) {
              return { ...cluster, detailedNodes: detailData.nodes };
            }
            return cluster;
          });
        });
        
        if (showModal) {
          setDetailModalVisible(true);
        }
      } else {
        console.error('获取集群详情失败:', response.data.message);
      }
    } catch (error) {
      console.error('获取集群详情错误:', error);
    } finally {
      if (showModal) {
        setDetailLoading(false);
      }
    }
  };

  // 删除集群
  const deleteCluster = async (clusterId) => {
    try {
      const response = await axios.delete(`http://localhost:5001/api/clusters/${clusterId}`);

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

  // 渲染树形结构的节点标题
  const renderTreeNodeTitle = (node) => (
    <Space>
      <DesktopOutlined />
      <span>{node.name}</span>
      <Tag color={node.status === 'online' ? 'green' : 'red'}>
        {node.status === 'online' ? '在线' : '离线'}
      </Tag>
      {node.gpus && (
        <Tag color="blue">
          GPU: {node.gpus.length}
        </Tag>
      )}
    </Space>
  );

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

  // 格式化内存大小显示
  const formatMemory = (memoryMB) => {
    if (!memoryMB) return '未知';
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
  
  // 计算GPU使用率 (模拟数据)
  const calculateGPUUsage = (gpuId) => {
    // 基于GPU ID生成一个伪随机数，使其对于同一个GPU保持一致
    const hash = gpuId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return Math.min(95, Math.max(5, (hash % 100))); // 范围在5-95之间
  };
  
  // 格式化GPU名称
  const formatGPUName = (name) => {
    if (name === 'Apple MacBook Pro GPU') {
      return 'M3 MAX';
    }
    return name;
  };

  // 渲染集群详情模态框
  const renderDetailModal = () => {
    if (!clusterDetail) return null;

    const nodes = clusterDetail.nodes || [];
    const totalGpus = nodes.reduce((sum, node) => sum + (node.gpus ? node.gpus.length : 0), 0);
    const totalCPUCores = nodes.reduce((acc, node) => {
      return acc + (node.cpu_info?.cores || 0);
    }, 0);
    const totalMemory = nodes.reduce((acc, node) => {
      return acc + (node.memory_total || 0);
    }, 0);

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
          <Card title="集群资源概览" bordered={false} size="small">
            <Row gutter={16}>
              <Col span={4}>
                <Statistic 
                  title="节点数量" 
                  value={nodes.length} 
                  prefix={<DesktopOutlined />} 
                  style={{ fontSize: '0.9em' }}
                />
              </Col>
              <Col span={4}>
                <Statistic 
                  title="GPU总数" 
                  value={totalGpus} 
                  prefix={<RocketOutlined />} 
                  style={{ fontSize: '0.9em' }}
                />
              </Col>
              <Col span={8}>
                <Statistic 
                  title="CPU核心总数" 
                  value={totalCPUCores || '未知'} 
                  prefix={<BarChartOutlined />} 
                  style={{ fontSize: '0.9em' }}
                />
              </Col>
              <Col span={8}>
                <Statistic 
                  title="内存总量" 
                  value={formatMemory(totalMemory)} 
                  prefix={<DatabaseOutlined />} 
                  style={{ fontSize: '0.9em' }}
                />
              </Col>
            </Row>
            <Row style={{ marginTop: 16 }}>
              <Col span={24}>
                <Statistic 
                  title="集群状态" 
                  value={clusterDetail.status === 'online' ? '在线' : '离线'} 
                  valueStyle={{ color: clusterDetail.status === 'online' ? '#52c41a' : '#ff4d4f' }}
                  prefix={clusterDetail.status === 'online' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                />
              </Col>
            </Row>
          </Card>

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
          <Title level={4} style={{ marginTop: 16 }}>节点资源详情</Title>
          {nodes.length === 0 ? (
            <Text type="secondary">暂无节点信息</Text>
          ) : (
            nodes.map((node, index) => (
              <Card 
                key={node.id} 
                title={
                  <Space>
                    <DesktopOutlined />
                    <span>节点: {node.name}</span>
                    <Tag color={node.status === 'online' ? 'green' : 'red'}>
                      {node.status === 'online' ? '在线' : '离线'}
                    </Tag>
                  </Space>
                }
                style={{ marginBottom: 16 }}
                type="inner"
              >
                <Tabs defaultActiveKey="overview">
                  <Tabs.TabPane tab="基本信息" key="overview">
                    <Row gutter={16}>
                      <Col span={12}>
                        <Descriptions bordered size="small" column={1} layout="vertical">
                          <Descriptions.Item label="节点ID">{node.id}</Descriptions.Item>
                          <Descriptions.Item label="IP地址">{node.ip}</Descriptions.Item>
                          <Descriptions.Item label="主机名">
                            {node.metadata?.hostname || '未知'}
                          </Descriptions.Item>
                          <Descriptions.Item label="操作系统">
                            {node.metadata?.os} {node.metadata?.os_version}
                          </Descriptions.Item>
                        </Descriptions>
                      </Col>
                      <Col span={12}>
                        <Card title="CPU信息" size="small" bordered={false}>
                          {node.cpu_info ? (
                            <>
                              <Descriptions bordered size="small" column={1}>
                                <Descriptions.Item label="CPU型号">
                                  {node.cpu_info.model || '未知'}
                                </Descriptions.Item>
                                <Descriptions.Item label="CPU核心数">
                                  {node.cpu_info.cores || '未知'}
                                </Descriptions.Item>
                                <Descriptions.Item label="CPU架构">
                                  {node.cpu_info.architecture || '未知'}
                                </Descriptions.Item>
                                <Descriptions.Item label="CPU厂商">
                                  {node.cpu_info.vendor || '未知'}
                                </Descriptions.Item>
                              </Descriptions>
                            </>
                          ) : (
                            <Text type="secondary">暂无CPU信息</Text>
                          )}
                        </Card>
                      </Col>
                    </Row>
                    
                    {/* 内存信息 */}
                    {(node.memory_total || node.memory_available) && (
                      <Card title="内存信息" size="small" style={{ marginTop: 16 }} bordered={false}>
                        <Row gutter={16} align="middle">
                          <Col span={6}>
                            <Statistic 
                              title="总内存" 
                              value={formatMemory(node.memory_total)} 
                              prefix={<DatabaseOutlined />}
                            />
                          </Col>
                          <Col span={6}>
                            <Statistic 
                              title="可用内存" 
                              value={formatMemory(node.memory_available)} 
                            />
                          </Col>
                          <Col span={12}>
                            <div style={{ marginBottom: 4 }}>内存使用率</div>
                            <Progress 
                              percent={calculateMemoryUsage(node.memory_total, node.memory_available)} 
                              status={calculateMemoryUsage(node.memory_total, node.memory_available) > 80 ? "exception" : "normal"}
                            />
                          </Col>
                        </Row>
                      </Card>
                    )}
                  </Tabs.TabPane>
                  
                  <Tabs.TabPane tab="GPU资源" key="gpu">
                    {node.gpus && node.gpus.length > 0 ? (
                      <Table
                        dataSource={node.gpus}
                        rowKey="id"
                        pagination={false}
                        columns={[
                          {
                            title: 'GPU名称',
                            dataIndex: 'name',
                            key: 'name',
                            render: (text) => <strong>{text}</strong>
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
                        ]}
                      />
                    ) : (
                      <Empty description="该节点没有GPU资源" />
                    )}
                  </Tabs.TabPane>
                </Tabs>


              </Card>
            ))
          )}
        </Spin>
      </Modal>
    );
  };

  // 构建层次树结构数据
  const buildTreeData = () => {
    return clusters.map(cluster => ({
      key: cluster.id,
      title: (
        <Space>
          <CloudServerOutlined style={{ fontSize: '18px', color: '#1890ff' }} />
          <span style={{ fontWeight: 'bold' }}>{cluster.name}</span>
          <Tag color={cluster.status === 'online' ? 'green' : 'red'}>
            {cluster.status === 'online' ? '在线' : '离线'}
          </Tag>
          <Tag color="purple">
            {cluster.adapter_type === 'apple' ? 'Apple Silicon' : 'NVIDIA'}
          </Tag>
          <Tag color="blue">
            节点: {cluster.nodes_count} | GPU: {cluster.gpus_count}
          </Tag>
          <Button 
            type="link" 
            size="small" 
            onClick={(e) => {
              e.stopPropagation();
              fetchClusterDetail(cluster.id);
            }}
          >
            查看详情
          </Button>
          <Button 
            type="link" 
            danger 
            size="small" 
            onClick={(e) => {
              e.stopPropagation();
              Modal.confirm({
                title: '确认删除',
                content: `确定要删除集群 "${cluster.name}" 吗？此操作不可恢复。`,
                onOk: () => deleteCluster(cluster.id)
              });
            }}
          >
            删除
          </Button>
        </Space>
      ),
      selectable: false,
      cluster: cluster
    }));
  };

  return (
    <div className="cluster-list">
      <Card
        title={
          <Space>
            <CloudServerOutlined />
            <span>计算集群层次结构</span>
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
        {loading ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin tip="加载中..." />
          </div>
        ) : clusters.length === 0 ? (
          <Empty description="暂无集群信息" />
        ) : (
          <List
            dataSource={clusters.map((cluster, index) => ({ ...cluster, clusterIndex: index + 1 }))}
            renderItem={cluster => (
              <List.Item>
                <Card 
                  title={
                    <Space>
                      <strong style={{ fontSize: '16px' }}>#{cluster.clusterIndex}</strong>
                      <CloudServerOutlined style={{ fontSize: '18px', color: '#1890ff' }} />
                      <span style={{ fontWeight: 'bold', fontSize: '16px' }}>{cluster.name}</span>
                      <Tag color={cluster.status === 'online' ? 'green' : 'red'}>
                        {cluster.status === 'online' ? '在线' : '离线'}
                      </Tag>
                      <Tag color="purple">
                        {cluster.adapter_type === 'apple' ? 'Apple Silicon' : 'NVIDIA'}
                      </Tag>
                    </Space>
                  }
                  extra={
                    <Space>
                      <Button 
                        type="primary" 
                        size="small" 
                        onClick={() => fetchClusterDetail(cluster.id)}
                      >
                        查看详情
                      </Button>
                      <Button 
                        danger 
                        size="small" 
                        onClick={() => {
                          Modal.confirm({
                            title: '确认删除',
                            content: `确定要删除集群 "${cluster.name}" 吗？此操作不可恢复。`,
                            onOk: () => deleteCluster(cluster.id)
                          });
                        }}
                      >
                        删除
                      </Button>
                    </Space>
                  }
                  style={{ width: '100%' }}
                >
                  <Row gutter={16}>
                    <Col span={3}>
                      <Statistic 
                        title="节点数量" 
                        value={cluster.nodes_count} 
                        prefix={<DesktopOutlined />} 
                        style={{ fontSize: '0.85em' }}
                      />
                    </Col>
                    <Col span={3}>
                      <Statistic 
                        title="GPU总数" 
                        value={cluster.gpus_count} 
                        prefix={<RocketOutlined />} 
                        style={{ fontSize: '0.85em' }}
                      />
                    </Col>
                    <Col span={18}>
                      <div style={{ marginBottom: 8 }}>
                        <strong>节点列表：</strong>
                      </div>
                      {/* 显示节点列表的详细信息 */}
                      {cluster.detailedNodes ? (
                        <Table
                          size="small"
                          bordered
                          dataSource={cluster.detailedNodes.map((node, idx) => ({ ...node, nodeIndex: idx + 1 }))}
                          rowKey="id"
                          pagination={false}
                          columns={[
                            {
                              title: '序号',
                              dataIndex: 'nodeIndex',
                              key: 'index',
                              width: 60,
                              render: (text) => <strong>#{text}</strong>
                            },
                            {
                              title: '节点名称',
                              dataIndex: 'name',
                              key: 'name',
                              render: (text, record) => (
                                <Space>
                                  <DesktopOutlined style={{ color: '#1890ff' }} />
                                  <span style={{ fontWeight: 'bold' }}>{text}</span>
                                  <Tag color={record.status === 'online' ? 'green' : 'red'}>
                                    {record.status === 'online' ? '在线' : '离线'}
                                  </Tag>
                                </Space>
                              )
                            },
                            {
                              title: 'CPU',
                              key: 'cpu',
                              width: 100,
                              render: (_, record) => (
                                <span>
                                  {record.cpu_info ? `${record.cpu_info.cores} 核` : '未知'}
                                </span>
                              )
                            },
                            {
                              title: '内存',
                              key: 'memory',
                              width: 180,
                              render: (_, record) => (
                                <span>
                                  {record.memory_total ? formatMemory(record.memory_total) : '未知'}
                                  {record.memory_total && record.memory_available && (
                                    <>
                                      <br />
                                      <Progress 
                                        percent={calculateMemoryUsage(record.memory_total, record.memory_available)} 
                                        size="small" 
                                        status={calculateMemoryUsage(record.memory_total, record.memory_available) > 80 ? "exception" : "normal"}
                                      />
                                    </>
                                  )}
                                </span>
                              )
                            },
                            {
                              title: 'GPU信息',
                              key: 'gpus',
                              render: (_, record) => (
                                <div>
                                  {record.gpus && record.gpus.length > 0 ? (
                                    <Table
                                      size="small"
                                      bordered
                                      dataSource={record.gpus.map((gpu, idx) => ({ ...gpu, gpuIndex: idx + 1 }))}
                                      rowKey="id"
                                      pagination={false}
                                      style={{ marginBottom: 0 }}
                                      columns={[
                                        {
                                          title: '序号',
                                          dataIndex: 'gpuIndex',
                                          key: 'gpuIndex',
                                          width: 50,
                                          render: (text) => <span style={{ fontSize: '0.9em' }}>#{text}</span>
                                        },
                                        {
                                          title: 'GPU名称',
                                          key: 'name',
                                          width: 100,
                                          render: (_, gpu) => (
                                            <Tag color="blue" style={{ fontSize: '0.9em' }}>{formatGPUName(gpu.name)}</Tag>
                                          )
                                        },
                                        {
                                          title: '显存',
                                          key: 'memory',
                                          width: 80,
                                          render: (_, gpu) => <span style={{ fontSize: '0.9em' }}>{formatMemory(gpu.memory_total)}</span>
                                        },
                                        {
                                          title: '占用率',
                                          key: 'usage',
                                          render: (_, gpu) => {
                                            const usage = calculateGPUUsage(gpu.id);
                                            return (
                                              <Progress 
                                                percent={usage} 
                                                size="small" 
                                                status={usage > 80 ? "exception" : "normal"}
                                                style={{ marginRight: 0 }}
                                              />
                                            );
                                          }
                                        }
                                      ]}
                                    />
                                  ) : (
                                    <span>无 GPU</span>
                                  )}
                                </div>
                              )
                            }
                          ]}
                        />
                      ) : (
                        <Spin tip="加载节点信息..." />
                      )}
                    </Col>
                  </Row>
                </Card>
              </List.Item>
            )}
          />
        )}
      </Card>

      {renderDetailModal()}
    </div>
  );
};

export default ClusterList;
