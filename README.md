# 模型部署信息表单 Demo

## 运行方式

### 1. 后端（Flask）
```bash
cd backend
pip install -r requirements.txt
python app.py
```
后端默认监听 `http://127.0.0.1:5000`

### 2. 前端（React）
```bash
cd frontend
npm install
npm start
```
前端默认监听 `http://localhost:3000`

---

- 表单提交后会将数据发送到后端 `/api/deploy`。
- 冷色调UI，适合展示模型部署相关信息。
