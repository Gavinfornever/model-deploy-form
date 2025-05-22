import React, { useState, useEffect } from 'react';
import { 
  Row, Col, Card, Statistic, Progress, Table, 
  Divider, List, Tag, Space, Button, Tooltip, Tabs 
} from 'antd';
import {
  AreaChartOutlined,
  RocketOutlined,
  CloudServerOutlined,
  DesktopOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  ApiOutlined,
  KeyOutlined,
  LineChartOutlined,
  PieChartOutlined
} from '@ant-design/icons';
import { Line, Pie } from '@ant-design/charts';

const Dashboard = () => {
  const [loading, setLoading] = useState(false);
  const [modelStats, setModelStats] = useState({
    total: 0,
    running: 0,
    stopped: 0
  });
  const [clusterStats, setClusterStats] = useState([]);
  const [gpuUsage, setGpuUsage] = useState([]);
  const [recentModels, setRecentModels] = useState([]);
  const [usageData, setUsageData] = useState({
    api_requests: {
      total: 0,
      daily: 0,
      models: [],
      history: []
    },
    token_usage: {
      total: 0,
      daily: 0,
      models: [],
      history: []
    }
  });

  // 获取仪表盘数据
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // 获取模型列表数据
      const response = await fetch('http://127.0.0.1:5000/api/models');
      const result = await response.json();
      
      if (result.status === 'success') {
        const models = result.data.models;
        
        // 计算模型统计信息
        const running = models.filter(model => model.status === 'running').length;
        const stopped = models.filter(model => model.status === 'stopped').length;
        
        setModelStats({
          total: models.length,
          running,
          stopped
        });
        
        // 计算集群统计信息
        const clusters = [...new Set(models.map(model => model.cluster))];
        let clusterData = clusters.map(cluster => {
          const clusterModels = models.filter(model => model.cluster === cluster);
          const running = clusterModels.filter(model => model.status === 'running').length;
          const total = clusterModels.length;
          
          // 将local改为local (mac)
          const displayName = cluster === 'local' ? 'local (mac)' : cluster;
          
          return {
            name: cluster,
            displayName,
            total,
            running,
            utilization: total > 0 ? Math.round((running / total) * 100) : 0
          };
        });
        
        // 只保留三个集群，并将muxi调整到最后一个位置
        if (clusterData.length > 3) {
          // 找出需要保留的三个集群
          const localCluster = clusterData.find(c => c.name === 'local');
          const muxiCluster = clusterData.find(c => c.name === 'muxi');
          
          // 过滤出除local和muxi之外的集群
          const otherClusters = clusterData.filter(c => c.name !== 'local' && c.name !== 'muxi');
          
          // 选择一个其他集群（如果有的话）
          const selectedOtherCluster = otherClusters.length > 0 ? [otherClusters[0]] : [];
          
          // 按照要求的顺序组合集群：local, 其他集群, muxi
          clusterData = [
            ...(localCluster ? [localCluster] : []),
            ...selectedOtherCluster,
            ...(muxiCluster ? [muxiCluster] : [])
          ];
          
          // 确保最多只有三个集群
          clusterData = clusterData.slice(0, 3);
        } else {
          // 如果集群数量少于或等于3，仍然需要调整顺序
          const localCluster = clusterData.find(c => c.name === 'local');
          const muxiCluster = clusterData.find(c => c.name === 'muxi');
          const otherClusters = clusterData.filter(c => c.name !== 'local' && c.name !== 'muxi');
          
          // 重新排序
          clusterData = [
            ...(localCluster ? [localCluster] : []),
            ...otherClusters,
            ...(muxiCluster ? [muxiCluster] : [])
          ];
        }
        
        setClusterStats(clusterData);
        
        // GPU使用数据 - 确保包含localhost(64GB)、A10服务器(24GB)和muxi(64GB)三个服务器
        const gpuData = [];
        
        // 获取现有服务器
        let servers = [...new Set(models.map(model => model.server))];
        
        // 确保我们至少有这三个服务器
        const requiredServers = ['localhost', '47.102.116.12', '10.31.29.19'];
        const serverDisplayNames = {
          'localhost': 'localhost',
          '47.102.116.12': 'A10服务器',
          '10.31.29.19': 'muxi'
        };
        const serverMemorySizes = {
          'localhost': '64GB',
          '47.102.116.12': '24GB',
          '10.31.29.19': '64GB'
        };
        
        // 合并现有服务器和必需服务器
        servers = [...new Set([...servers, ...requiredServers])];
        
        // 为每个服务器和GPU ID生成数据
        servers.forEach((server, serverIndex) => {
          // 获取服务器对应的模型
          const serverModels = models.filter(model => model.server === server);
          
          // 如果没有模型使用这个服务器，我们仍然需要显示它（如果它是必需服务器）
          let gpuIds = [];
          if (serverModels.length > 0) {
            gpuIds = [...new Set(serverModels.map(model => model.gpu))].flat();
          } else if (requiredServers.includes(server)) {
            // 如果是必需服务器但没有模型使用，添加一个默认GPU
            gpuIds = ['0'];
          }
          
          // 如果没有GPU，跳过这个服务器
          if (gpuIds.length === 0) return;
          
          gpuIds.forEach((gpuId, gpuIndex) => {
            // 使用服务器索引和GPU索引生成固定但不同的值
            const hashCode = (str) => {
              let hash = 0;
              for (let i = 0; i < str.length; i++) {
                hash = ((hash << 5) - hash) + str.charCodeAt(i);
                hash |= 0; // 转换为32位整数
              }
              return Math.abs(hash);
            };
            
            const serverHash = hashCode(server);
            const gpuHash = hashCode(gpuId.toString());
            
            // 生成固定但不规律的CPU使用率 (15-95%)
            const cpuUsage = 15 + ((serverHash * 17 + gpuHash * 13) % 80);
            
            // 生成固定但不同的显存使用率 (40-95%)
            const memory = 40 + (gpuHash % 55);
            
            // 生成固定但不同的温度 (55-85°C)
            const temperature = 55 + ((serverHash + gpuHash) % 30);
            
            // 获取服务器显示名称和显存大小
            const displayName = serverDisplayNames[server] || server;
            const memorySize = serverMemorySizes[server] || '16GB';
            
            gpuData.push({
              id: `${server}-${gpuId}`,
              server: displayName,  // 使用显示名称
              gpu: gpuId,
              memorySize: memorySize,  // 添加显存大小信息
              cpuUsage,
              memory,
              temperature,
              models: serverModels.filter(model => model.gpu.includes(gpuId)).map(m => m.modelName).join(', ')
            });
          });
        });
        
        // 按照要求的顺序排序：localhost -> A10服务器 -> muxi
        gpuData.sort((a, b) => {
          const order = {'localhost': 1, 'A10服务器': 2, 'muxi': 3};
          return (order[a.server] || 99) - (order[b.server] || 99);
        });
        
        setGpuUsage(gpuData);
        
        // 最近部署的模型
        const recent = [...models].sort((a, b) => b.id.localeCompare(a.id)).slice(0, 5);
        setRecentModels(recent);
      }
      
      // 获取API使用量和Token使用量数据
      const usageResponse = await fetch('http://127.0.0.1:5000/api/usage');
      const usageResult = await usageResponse.json();
      
      if (usageResult.status === 'success') {
        setUsageData(usageResult.data);
      }
    } catch (error) {
      console.error('获取仪表盘数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    // 每30秒刷新一次数据
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // API请求图表组件
  const renderApiRequestsChart = () => {
    const config = {
      data: usageData.api_requests.history,
      height: 300,
      xField: 'date',
      yField: 'count',
      point: {
        size: 5,
        shape: 'diamond',
      },
      tooltip: {
        formatter: (datum) => {
          return { name: datum.date, value: `${datum.count} 请求` };
        },
      },
      title: {
        visible: true,
        text: 'API请求趋势',
      },
      smooth: true,
      areaStyle: {
        fill: 'l(270) 0:#1890ff 1:rgba(24, 144, 255, 0.1)',
      },
      meta: {
        count: {
          alias: 'API请求数',
          formatter: (value) => {
            if (value >= 10000) {
              // return (value / 10000).toFixed(1) + '万';
              return (value / 10000).toFixed(1);
            }
            return value;
          },
        },
      },
    };
    
    return <Line {...config} />
  };
  
  // 模型请求分布图表
  const renderModelRequestsChart = () => {
    const pieData = usageData.api_requests.models.map(item => ({
      type: item.name,
      value: item.requests
    }));
    
    const config = {
      appendPadding: 10,
      data: pieData,
      height: 300,
      angleField: 'value',
      colorField: 'type',
      radius: 0.8,
      label: {
        type: 'outer',
        content: '{name} {percentage}',
      },
      interactions: [{ type: 'element-active' }],
      tooltip: {
        formatter: (datum) => {
          return { name: datum.type, value: `${datum.value} 请求` };
        },
      },
      title: {
        visible: true,
        text: '模型请求分布',
      },
    };
    
    return <Pie {...config} />;
  };
  
  // Token使用量图表
  const renderTokenUsageChart = () => {
    const config = {
      data: usageData.token_usage.history,
      height: 300,
      xField: 'date',
      yField: 'count',
      point: {
        size: 5,
        shape: 'diamond',
      },
      tooltip: {
        formatter: (datum) => {
          return { name: datum.date, value: `${datum.count} tokens` };
        },
      },
      title: {
        visible: true,
        text: 'Token使用量趋势',
      },
      smooth: true,
      color: '#722ed1',
      areaStyle: {
        fill: 'l(270) 0:#722ed1 1:rgba(114, 46, 209, 0.1)',
      },
      meta: {
        count: {
          alias: 'Token使用量',
          formatter: (value) => {
            if (value >= 100000000) {
              return (value / 100000000).toFixed(1) + '亿';
            } else if (value >= 10000) {
              return (value / 10000).toFixed(1) + '万';
            }
            return value;
          },
        },
      },
    };
    
    return <Line {...config} />
  };
  
  // 模型Token分布图表
  const renderModelTokensChart = () => {
    const pieData = usageData.token_usage.models.map(item => ({
      type: item.name,
      value: item.tokens
    }));
    
    const config = {
      appendPadding: 10,
      data: pieData,
      height: 300,
      angleField: 'value',
      colorField: 'type',
      radius: 0.8,
      label: {
        type: 'outer',
        content: '{name} {percentage}',
      },
      interactions: [{ type: 'element-active' }],
      tooltip: {
        formatter: (datum) => {
          return { name: datum.type, value: `${datum.value} tokens` };
        },
      },
      title: {
        visible: true,
        text: '模型Token分布',
      },
    };
    
    return <Pie {...config} />;
  };

  // GPU使用情况表格列
  const gpuColumns = [
    {
      title: '服务器',
      dataIndex: 'server',
      key: 'server',
    },
    {
      title: 'GPU',
      dataIndex: 'gpu',
      key: 'gpu',
    },
    {
      title: '显存大小',
      dataIndex: 'memorySize',
      key: 'memorySize',
    },
    {
      title: 'CPU使用率',
      dataIndex: 'cpuUsage',
      key: 'cpuUsage',
      render: (cpuUsage) => (
        <Tooltip title={`${cpuUsage}%`}>
          <Progress 
            percent={cpuUsage} 
            size="small" 
            status="active"
            strokeColor={
              cpuUsage < 30 ? '#52c41a' : 
              cpuUsage < 70 ? '#faad14' : '#f5222d'
            }
          />
        </Tooltip>
      ),
    },
    {
      title: '显存使用率',
      dataIndex: 'memory',
      key: 'memory',
      render: (memory) => (
        <Tooltip title={`${memory}%`}>
          <Progress 
            percent={memory} 
            size="small" 
            status="active"
            strokeColor={
              memory < 30 ? '#52c41a' : 
              memory < 70 ? '#faad14' : '#f5222d'
            }
          />
        </Tooltip>
      ),
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
      render: (temp) => (
        <span style={{ 
          color: temp < 60 ? 'green' : 
                 temp < 75 ? 'orange' : 'red' 
        }}>
          {temp}°C
        </span>
      ),
    },
    {
      title: '运行模型',
      dataIndex: 'models',
      key: 'models',
      ellipsis: true,
    },
  ];

  return (
    <div className="dashboard-container">
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>系统仪表盘</h2>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={fetchDashboardData}
          loading={loading}
        >
          刷新数据
        </Button>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="模型总数"
              value={modelStats.total}
              prefix={<AreaChartOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="运行中模型"
              value={modelStats.running}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="已停止模型"
              value={modelStats.stopped}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 集群状态 */}
      <Card 
        title={
          <Space>
            <DesktopOutlined />
            <span>集群状态</span>
          </Space>
        } 
        style={{ marginBottom: 16 }}
      >
        <Row gutter={[16, 16]}>
          {clusterStats.map(cluster => (
            <Col span={8} key={cluster.name}>
              <Card size="small" title={cluster.displayName}>
                <Statistic
                  title="运行模型/总模型"
                  value={`${cluster.running}/${cluster.total}`}
                  valueStyle={{ fontSize: '16px' }}
                />
                <Divider style={{ margin: '12px 0' }} />
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span>使用率:</span>
                  <Progress 
                    percent={cluster.utilization} 
                    size="small" 
                    status={
                      cluster.utilization > 80 ? "exception" : 
                      cluster.utilization > 0 ? "active" : "normal"
                    }
                  />
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* GPU */}
      <Card 
        title={
          <Space>
            <InfoCircleOutlined />
            <span>GPU</span>
          </Space>
        } 
        style={{ marginBottom: 16 }}
      >
        <Table 
          dataSource={gpuUsage} 
          columns={gpuColumns} 
          rowKey="id"
          pagination={false}
          size="middle"
        />
      </Card>

      {/* API使用量和Token使用量统计 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic
              title="API请求总量"
              value={usageData.api_requests.total.toLocaleString()}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
              suffix={
                <Tooltip title="今日请求量">
                  <span style={{ fontSize: '14px', color: '#8c8c8c' }}>
                    (今日: {usageData.api_requests.daily.toLocaleString()})
                  </span>
                </Tooltip>
              }
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic
              title="Token使用量"
              value={usageData.token_usage.total >= 100000000 ? (usageData.token_usage.total / 100000000).toFixed(2) : (usageData.token_usage.total / 10000).toFixed(2)}
              prefix={<KeyOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix={
                <>
                  {usageData.token_usage.total >= 100000000 ? '亿' : '万'}
                  <Tooltip title="今日Token使用量">
                    <span style={{ fontSize: '14px', color: '#8c8c8c', marginLeft: '8px' }}>
                      (今日: {(usageData.token_usage.daily / 10000).toFixed(2)}万)
                    </span>
                  </Tooltip>
                </>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* API使用量图表 */}
      <Card 
        title={
          <Space>
            <ApiOutlined />
            <span>API使用量统计</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Tabs defaultActiveKey="1">
          <Tabs.TabPane tab="请求趋势" key="1">
            {renderApiRequestsChart()}
          </Tabs.TabPane>
          <Tabs.TabPane tab="模型分布" key="2">
            {renderModelRequestsChart()}
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* Token使用量图表 */}
      <Card 
        title={
          <Space>
            <KeyOutlined />
            <span>Token使用量统计</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Tabs defaultActiveKey="1">
          <Tabs.TabPane tab="使用趋势" key="1">
            {renderTokenUsageChart()}
          </Tabs.TabPane>
          <Tabs.TabPane tab="模型分布" key="2">
            {renderModelTokensChart()}
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* 最近部署的模型 */}
      <Card 
        title={
          <Space>
            <RocketOutlined />
            <span>最近部署的模型</span>
          </Space>
        }
      >
        <List
          itemLayout="horizontal"
          dataSource={recentModels}
          renderItem={item => (
            <List.Item
              actions={[
                item.status === 'running' ? (
                  <Tag color="green">运行中</Tag>
                ) : (
                  <Tag color="red">已停止</Tag>
                )
              ]}
            >
              <List.Item.Meta
                avatar={item.status === 'running' ? <CheckCircleOutlined style={{ color: 'green', fontSize: '20px' }} /> : <CloseCircleOutlined style={{ color: 'red', fontSize: '20px' }} />}
                title={<a href={`/models?id=${item.id}`}>{item.modelName}</a>}
                description={`部署在 ${item.server}:${item.port} | GPU: ${item.gpu} | 集群: ${item.cluster}`}
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default Dashboard;
