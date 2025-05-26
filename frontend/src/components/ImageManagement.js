import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, DatePicker, message, Space, Popconfirm, Typography, Tooltip, Upload } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, DeploymentUnitOutlined, UploadOutlined, CodeOutlined, LinkOutlined } from '@ant-design/icons';
import moment from 'moment';
import axios from 'axios';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { prism } from 'react-syntax-highlighter/dist/esm/styles/prism';

const { Title } = Typography;
const { Option } = Select;

const ImageManagement = () => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingImage, setEditingImage] = useState(null);
  const [form] = Form.useForm();
  const [searchText, setSearchText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [codeViewVisible, setCodeViewVisible] = useState(false);
  const [currentCode, setCurrentCode] = useState('');
  
  // 处理使用镜像部署
  const handleDeployWithImage = (image) => {
    // 使用 localStorage 临时存储选中的镜像，以便在部署页面使用
    localStorage.setItem('selectedImage', JSON.stringify(image));
    // 跳转到部署页面
    window.location.href = '/deploy';
  };

  // 模拟数据
  const mockImages = [
    {
      id: 1,
      name: 'vllm_image',
      version: 'v3',
      size: '5.2GB',
      createDate: '2025-04-15',
      creator: '张三',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 vllm==0.2.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000',
      ossUrl: 'oss://images/vllm/vllm_image_v3.tar'
    },
    {
      id: 13,
      name: 'transformers',
      version: 'v2',
      size: '4.8GB',
      createDate: '2025-05-23',
      creator: '王高',
      dockerfileContent: 'FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.1.0 transformers==4.36.0 accelerate==0.25.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000',
      ossUrl: 'oss://images/transformers/transformers_v2.tar'
    },
    {
      id: 2,
      name: 'huggingface_image',
      version: 'v2',
      size: '3.8GB',
      createDate: '2025-04-10',
      creator: '李四',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 transformers==4.30.2 huggingface_hub==0.16.4\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 7860',
      ossUrl: 'oss://images/huggingface/huggingface_v2.tar'
    },
    {
      id: 3,
      name: 'pytorch_image',
      version: 'v2.1',
      size: '4.5GB',
      createDate: '2025-04-12',
      creator: '王五',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8080',
      ossUrl: 'oss://images/pytorch_image/pytorch_v2.1.tar'
    },
    {
      id: 4,
      name: 'tensorflow_image',
      version: 'v2.0',
      size: '6.1GB',
      createDate: '2025-04-08',
      creator: '赵六',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install tensorflow==2.12.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8501',
      ossUrl: 'oss://images/tensorflow_image/tensorflow_v2.0.tar'
    },
    {
      id: 5,
      name: 'llama_image',
      version: 'v2',
      size: '8.3GB',
      createDate: '2025-04-05',
      creator: '张三',
      dockerfileContent: 'FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.1.0 transformers==4.36.0 accelerate==0.25.0 bitsandbytes==0.41.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 7860',
      ossUrl: 'oss://images/llama_image/llama_v2.tar'
    },
    {
      id: 6,
      name: 'bert_image',
      version: 'v1.5',
      size: '2.7GB',
      createDate: '2025-04-18',
      creator: '李四',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 transformers==4.30.2 sentence-transformers==2.2.2\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000',
      ossUrl: 'oss://images/bert_image/bert_v1.5.tar'
    },
    {
      id: 7,
      name: 'gpt_image',
      version: 'v3.5',
      size: '9.2GB',
      createDate: '2025-04-03',
      creator: '王五',
      dockerfileContent: 'FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.1.0 transformers==4.36.0 accelerate==0.25.0 flash-attn==2.3.4\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000',
      ossUrl: 'oss://text_generation/gpt/gpt_image.v3.5.tar'
    },
    {
      id: 8,
      name: 'stable_diffusion_image',
      version: 'v2.1',
      size: '7.5GB',
      createDate: '2025-04-07',
      creator: '赵六',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 diffusers==0.21.4 transformers==4.30.2 accelerate==0.20.3\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 7860',
      ossUrl: 'oss://image_generation/stable_diffusion/stable_diffusion_image.v2.1.tar'
    },
    {
      id: 9,
      name: 'milvus_image',
      version: 'v2.2',
      size: '3.2GB',
      createDate: '2025-04-14',
      creator: '张三',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip\n\nRUN pip3 install pymilvus==2.2.8 numpy==1.24.3\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 19530\nEXPOSE 19121',
      ossUrl: 'oss://vector_db/milvus/milvus_image.v2.2.tar'
    },
    {
      id: 10,
      name: 'faiss_image',
      version: 'v1.7',
      size: '2.1GB',
      createDate: '2025-04-16',
      creator: '李四',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip\n\nRUN pip3 install faiss-gpu==1.7.4 numpy==1.24.3\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8080',
      ossUrl: 'oss://vector_db/faiss/faiss_image.v1.7.tar'
    },
    {
      id: 11,
      name: 'onnx_image',
      version: 'v1.14',
      size: '1.8GB',
      createDate: '2025-04-19',
      creator: '王五',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip\n\nRUN pip3 install onnx==1.14.0 onnxruntime-gpu==1.15.1\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8080',
      ossUrl: 'oss://inference/onnx/onnx_image.v1.14.tar'
    },
    {
      id: 12,
      name: 'triton_image',
      version: 'v2.3',
      size: '4.3GB',
      createDate: '2025-04-11',
      creator: '赵六',
      dockerfileContent: 'FROM nvcr.io/nvidia/tritonserver:23.04-py3\n\nWORKDIR /app\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\nEXPOSE 8001\nEXPOSE 8002',
      ossUrl: 'oss://inference/triton/triton_image.v2.3.tar'
    },
    {
      id: 13,
      name: 'cuda_image',
      version: 'v12.1',
      cluster: 'A100集群',
      size: '5.7GB',
      createDate: '2025-04-09',
      creator: '张三'
    },
    {
      id: 14,
      name: 'cudnn_image',
      version: 'v8.9',
      size: '4.9GB',
      createDate: '2025-04-06',
      creator: '李四',
      dockerfileContent: 'FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip\n\nRUN pip3 install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8080',
      ossUrl: 'oss://base/cudnn/cudnn_image.v8.9.tar'
    },
    {
      id: 15,
      name: 'jupyter_image',
      version: 'v7.0',
      size: '2.3GB',
      createDate: '2025-04-17',
      creator: '王五',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip\n\nRUN pip3 install jupyter==1.0.0 jupyterlab==4.0.5 numpy==1.24.3 pandas==2.0.3 matplotlib==3.7.2\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8888\n\nCMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser"]',
      ossUrl: 'oss://tools/jupyter/jupyter_image.v7.0.tar'
    },
    {
      id: 16,
      name: 'ray_image',
      version: 'v2.5',
      size: '3.6GB',
      createDate: '2025-04-13',
      creator: '赵六',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip\n\nRUN pip3 install ray==2.5.1 ray[serve]==2.5.1 torch==2.0.1\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\nEXPOSE 8265\n\nCMD ["python3", "ray_server.py"]',
      ossUrl: 'oss://distributed/ray/ray_image.v2.5.tar'
    },
    {
      id: 17,
      name: 'langchain_image',
      version: 'v0.8',
      size: '1.5GB',
      createDate: '2025-04-20',
      creator: '张三',
      dockerfileContent: 'FROM python:3.10-slim\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y build-essential\n\nRUN pip3 install langchain==0.0.267 langchain-openai==0.0.2 fastapi==0.103.1 uvicorn==0.23.2\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\n\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]',
      ossUrl: 'https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/langchain_image/v0.8/langchain_image.tar'
    },
    {
      id: 18,
      name: 'transformers_image',
      version: 'v4.30',
      size: '3.1GB',
      createDate: '2025-04-04',
      creator: '李四',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 transformers==4.30.2 accelerate==0.20.3\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\n\nCMD ["python3", "transformers_server.py"]',
      ossUrl: 'https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/transformers_image/v4.30/transformers_image.tar'
    },
    {
      id: 19,
      name: 'deepspeed_image',
      version: 'v0.9',
      size: '4.2GB',
      createDate: '2025-04-02',
      creator: '王五',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 deepspeed==0.9.5 transformers==4.30.2\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\n\nCMD ["python3", "deepspeed_server.py"]',
      ossUrl: 'https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/deepspeed_image/v0.9/deepspeed_image.tar'
    },
    {
      id: 20,
      name: 'accelerate_image',
      version: 'v0.21',
      size: '1.9GB',
      createDate: '2025-04-01',
      creator: '赵六',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 accelerate==0.21.0 transformers==4.30.2\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\n\nCMD ["python3", "accelerate_server.py"]',
      ossUrl: 'https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/accelerate_image/v0.21/accelerate_image.tar'
    },
    {
      id: 21,
      name: 'diffusers_image',
      version: 'v0.18',
      size: '5.5GB',
      createDate: '2025-03-30',
      creator: '张三',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 diffusers==0.18.2 transformers==4.30.2 accelerate==0.20.3\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 7860\n\nCMD ["python3", "gradio_app.py"]',
      ossUrl: 'https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/diffusers_image/v0.18/diffusers_image.tar'
    },
    {
      id: 22,
      name: 'bitsandbytes_image',
      version: 'v0.40',
      size: '1.2GB',
      createDate: '2025-03-28',
      creator: '李四',
      dockerfileContent: 'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip git\n\nRUN pip3 install torch==2.0.1 bitsandbytes==0.40.0 transformers==4.30.2 accelerate==0.20.3\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nEXPOSE 8000\n\nCMD ["python3", "bnb_server.py"]',
      ossUrl: 'https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/bitsandbytes_image/v0.40/bitsandbytes_image.tar'
    }
  ];

  // 获取镜像列表
  const fetchImages = async () => {
    setLoading(true);
    try {
      // 从后端API获取镜像数据
      const response = await axios.get('http://127.0.0.1:5000/api/images');
      
      if (response.data && response.data.status === 'success' && response.data.data) {
        console.log('从后端获取镜像数据:', response.data.data);
        // 确保数据中有dockerfileContent和ossUrl字段
        const processedData = response.data.data.map(item => {
          if (!item.dockerfileContent) {
            item.dockerfileContent = mockImages.find(mock => mock.id === item.id)?.dockerfileContent || 
              'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nRUN apt-get update && apt-get install -y python3 python3-pip\n\nCOPY . .\n\nRUN pip3 install -r requirements.txt\n\nCMD ["python3", "app.py"]';
          }
          if (!item.ossUrl && item.id <= 22) {
            item.ossUrl = mockImages.find(mock => mock.id === item.id)?.ossUrl || 
              `https://model-deploy-images.oss-cn-beijing.aliyuncs.com/images/${item.name}/${item.version}/${item.name}.tar`;
          }
          return item;
        });
        setImages(processedData);
      } else {
        console.error('获取镜像数据失败:', response.data);
        // 如果获取失败，使用模拟数据
        setImages(mockImages);
      }
    } catch (error) {
      console.error('获取镜像列表失败:', error);
      message.error('获取镜像列表失败');
      // 如果获取失败，使用模拟数据
      setImages(mockImages);
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    fetchImages();
  }, []);

  // 添加或更新镜像
  const handleSaveImage = async (values) => {
    try {
      if (editingImage) {
        // 更新镜像
        const response = await axios.put(`http://127.0.0.1:5000/api/images/${editingImage.id}`, values);
        
        if (response.data && response.data.status === 'success') {
          message.success('镜像更新成功');
          // 重新获取镜像列表
          fetchImages();
        } else {
          message.error(response.data.message || '镜像更新失败');
        }
      } else {
        // 添加镜像
        const imageData = {
          ...values,
          createDate: moment().format('YYYY-MM-DD')
        };
        
        // 如果有上传的镜像文件，需要使用FormData
        if (imageFile) {
          const formData = new FormData();
          formData.append('file', imageFile);
          
          // 添加其他表单数据
          Object.keys(imageData).forEach(key => {
            formData.append(key, imageData[key]);
          });
          
          const response = await axios.post('http://127.0.0.1:5000/api/images/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          });
          
          if (response.data && response.data.status === 'success') {
            message.success('镜像添加成功');
            // 重新获取镜像列表
            fetchImages();
          } else {
            message.error(response.data.message || '镜像添加失败');
          }
        } else {
          // 没有上传文件，直接添加镜像信息
          const response = await axios.post('http://127.0.0.1:5000/api/images', imageData);
          
          if (response.data && response.data.status === 'success') {
            message.success('镜像添加成功');
            // 重新获取镜像列表
            fetchImages();
          } else {
            message.error(response.data.message || '镜像添加失败');
          }
        }
      }
      setModalVisible(false);
      form.resetFields();
      setEditingImage(null);
      setImageFile(null);
    } catch (error) {
      console.error('保存镜像失败:', error);
      message.error('保存镜像失败');
    }
  };

  // 删除镜像
  const handleDeleteImage = async (id) => {
    try {
      const response = await axios.delete(`http://127.0.0.1:5000/api/images/${id}`);
      
      if (response.data && response.data.status === 'success') {
        message.success('镜像删除成功');
        // 重新获取镜像列表
        fetchImages();
      } else {
        message.error(response.data.message || '镜像删除失败');
      }
    } catch (error) {
      console.error('删除镜像失败:', error);
      message.error('删除镜像失败');
    }
  };

  // 编辑镜像
  const handleEditImage = (record) => {
    setEditingImage(record);
    // 兼容处理，如果记录中有creator字段但没有creator_id字段
    const formData = {
      ...record,
      createDate: moment(record.createDate),
      creator_id: record.creator_id || record.creator
    };
    form.setFieldsValue(formData);
    setModalVisible(true);
  };

  // 添加新镜像
  const handleAddImage = () => {
    setEditingImage(null);
    form.resetFields();
    setImageFile(null);
    setModalVisible(true);
  };

  // 搜索过滤
  const filteredImages = images.filter(
    img => 
      img.name.toLowerCase().includes(searchText.toLowerCase()) ||
      img.version.toLowerCase().includes(searchText.toLowerCase()) ||
      img.cluster?.includes(searchText) ||
      (img.creator_id && img.creator_id.includes(searchText))
  );

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '镜像名称',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      sorter: (a, b) => a.version.localeCompare(b.version),
    },
    {
      title: 'OSS地址',
      dataIndex: 'ossUrl',
      key: 'ossUrl',
      render: (text) => text || '无',
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (text) => text || '未知',
    },
    {
      title: '镜像构建代码',
      dataIndex: 'dockerfileContent',
      key: 'dockerfileContent',
      render: (text) => (
        <Button 
          type="link" 
          onClick={() => {
            setCurrentCode(text || '# 无构建代码');
            setCodeViewVisible(true);
          }}
        >
          <CodeOutlined /> 查看代码
        </Button>
      ),
    },
    {
      title: '创建日期',
      dataIndex: 'createDate',
      key: 'createDate',
      sorter: (a, b) => moment(a.createDate).unix() - moment(b.createDate).unix(),
    },
    {
      title: '创建者',
      dataIndex: 'creator_name',  // 将使用后端返回的creator_name字段
      key: 'creator_name',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            icon={<DeploymentUnitOutlined />} 
            size="small"
            onClick={() => handleDeployWithImage(record)}
          >
            部署
          </Button>
          <Button 
            type="default" 
            icon={<EditOutlined />} 
            size="small"
            onClick={() => handleEditImage(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个镜像吗？"
            onConfirm={() => handleDeleteImage(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="primary" 
              danger 
              icon={<DeleteOutlined />} 
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>镜像管理</Title>
        <div>
          <Input
            placeholder="搜索镜像"
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            style={{ width: 200, marginRight: 16 }}
            prefix={<SearchOutlined />}
          />
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleAddImage}
          >
            添加镜像
          </Button>
        </div>
      </div>
      
      <Table
        columns={columns}
        dataSource={filteredImages}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
        bordered
      />

      {/* 添加/编辑镜像的模态框 */}
      <Modal
        title={editingImage ? '编辑镜像' : '添加镜像'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setImageFile(null);
        }}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveImage}
        >
          <div style={{ display: 'flex', gap: '16px' }}>
            <Form.Item
              name="name"
              label="镜像名称"
              rules={[{ required: true, message: '请输入镜像名称' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="请输入镜像名称" />
            </Form.Item>
            
            <Form.Item
              name="version"
              label="版本"
              rules={[{ required: true, message: '请输入版本' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="请输入版本，例如：v1.0" />
            </Form.Item>
          </div>
          
          <div style={{ display: 'flex', gap: '16px' }}>
            <Form.Item
              name="createDate"
              label="创建日期"
              rules={[{ required: true, message: '请选择创建日期' }]}
              style={{ flex: 1 }}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            
            <Form.Item
              name="size"
              label="大小"
              rules={[{ required: true, message: '请输入大小' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="请输入大小，例如：5.2GB" />
            </Form.Item>
          </div>
          
          <div style={{ display: 'flex', gap: '16px' }}>
            <Form.Item
              name="ossUrl"
              label="OSS地址"
              rules={[{ required: false, message: '请输入OSS地址' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="上传文件后会自动生成OSS地址" disabled />
            </Form.Item>
            
            {/* 创建者ID字段已移除，由后端自动处理 */}
          </div>
          
          <Form.Item
            name="dockerfileContent"
            label="镜像构建代码"
            rules={[{ required: true, message: '请输入Dockerfile内容' }]}
          >
            <Input.TextArea 
              placeholder="请输入Dockerfile内容" 
              autoSize={{ minRows: 6, maxRows: 10 }}
              style={{ fontFamily: 'monospace', backgroundColor: '#f5f5f5' }}
              defaultValue={'FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04\n\nWORKDIR /app\n\nCOPY . .\n\nRUN apt-get update && apt-get install -y python3 python3-pip\n\nRUN pip3 install -r requirements.txt\n\nCMD ["python3", "app.py"]'}
            />
          </Form.Item>
          
          <Form.Item
            name="imageFile"
            label="上传镜像文件（可选）"
            valuePropName="fileList"
            getValueFromEvent={(e) => {
              if (Array.isArray(e)) {
                return e;
              }
              return e && e.fileList;
            }}
          >
            <Upload
              beforeUpload={(file) => {
                setImageFile(file);
                return false; // 阻止自动上传
              }}
              onRemove={() => {
                setImageFile(null);
              }}
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>选择镜像tar文件</Button>
              <div style={{ marginTop: 8, color: '#888' }}>
                支持上传.tar格式的Docker镜像文件
              </div>
            </Upload>
          </Form.Item>
          
          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button 
                style={{ marginRight: 8 }} 
                onClick={() => {
                  setModalVisible(false);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>

      {/* 代码查看模态框 */}
      <Modal
        title="镜像构建代码"
        open={codeViewVisible}
        onCancel={() => setCodeViewVisible(false)}
        footer={null}
        width={800}
      >
        <SyntaxHighlighter 
          language="dockerfile" 
          style={prism} 
          customStyle={{ 
            borderRadius: '4px', 
            padding: '10px', 
            maxHeight: '500px',
            backgroundColor: '#f5f5f5' 
          }}
          wrapLines={true}
          wrapLongLines={true}
          showLineNumbers={true}
        >
          {currentCode}
        </SyntaxHighlighter>
      </Modal>
    </div>
  );
};

export default ImageManagement;
