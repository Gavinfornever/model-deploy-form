# center_controller.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Optional
import requests
import threading
import time
import argparse
import uvicorn
import aiohttp
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI()

# 存储所有 cluster controller 的信息
clusters = {}

# ------------------- 数据结构 -------------------
class ClusterInfo(BaseModel):
    cluster_id: str
    ip: str
    port: Optional[str] = None
    last_heartbeat: float = time.time()
    meta: Dict = {}

class RegisterClusterRequest(BaseModel):
    ip: str
    port: Optional[str] = None
    cluster_id: str

class DeployModelRequest(BaseModel):
    model_config_id: str
    cluster_id: Optional[str] = None
    image_id: Optional[str] = None
    name: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[str] = None
    node_id: Optional[str] = None
    gpu_devices: Optional[str] = None
    backend: Optional[str] = None

# ------------------- 注册相关 -------------------
@app.get("/register/cluster")
def register_cluster(req: RegisterClusterRequest):
    key = req.cluster_id
    clusters[key] = ClusterInfo(**req.dict())
    return {"status_code": 200, "msg": "Cluster registered"}

@app.get("/heartbeat")
def heartbeat(cluster_id: str):
    if cluster_id in clusters:
        clusters[cluster_id].last_heartbeat = time.time()
        return {"status_code": 200, "msg": "Heartbeat updated"}
    else:
        return {"status_code": 404, "msg": "Cluster not found"}

# ------------------- Dashboard/Cluster -------------------
@app.get("/dashboard")
def dashboard():
    # 聚合所有 cluster 信息
    num_cluster = len(clusters)
    num_model = 0
    num_instance = 0
    num_model_config = 0
    gpu_utilization = {}
    cpu_utilization = {}
    # 可以遍历 clusters，向各 cluster controller 拉取数据聚合
    # 这里只做示例
    return {
        "result": {
            "num_model": num_model,
            "num_instance": num_instance,
            "num_cluster": num_cluster,
            "num_model_config": num_model_config,
            "gpu_utilization": gpu_utilization,
            "cpu_utilization": cpu_utilization,
        },
        "msg": "success"
    }

# ------------------- 模型相关接口 -------------------
@app.post("/model/deploy")
def deploy_model(req: DeployModelRequest):
    # 选择 cluster
    cluster = clusters.get(req.cluster_id)
    if not cluster:
        raise HTTPException(404, "Cluster not found")
    url = f"http://{cluster.ip}:{cluster.port}/deploy"
    # 透传到 cluster controller
    resp = requests.post(url, json=req.dict())
    return resp.json()

fetch_timeout = aiohttp.ClientTimeout(total=3 * 3600)
async def fetch_remote(url, pload=None, name=None):
    async with aiohttp.ClientSession(timeout=fetch_timeout) as session:
        async with session.post(url, json=pload) as response:
            chunks = []
            if response.status != 200:
                ret = {
                    "text": await response.text(),
                    "error_code": ErrorCode.INTERNAL_ERROR,
                }
                return ret
            if "deploy" in url:
                ret={
                    "text": await response.text(),
                    "code":200
                }
                return ret

            async for chunk, _ in response.content.iter_chunks():
                chunks.append(chunk)
        output = b"".join(chunks)
    # 貌似是异步的问题 controller那边多了一会拿到了值，但这边却直接返回了，没有足够等待
    if name is not None:
        res = json.loads(output)
        if name != "":
            res = res[name]
        return res

    return output

from utils import DeployCommand
@app.post("/model/deploy3")
async def deploy_model(params: DeployCommand):
    print(params)
    controller_address = ""
    print(controller_address)
    url=f"http://localhost:20091/deploy"
    response=await fetch_remote(url, params.__dict__)
    return JSONResponse(status_code=200, content="success")

@app.post("/model/instance")
def add_instance(model_id: str):
    # TODO: 透传到对应 cluster controller
    return {"result": {}, "status_code": 200, "msg": "Instance added"}

@app.delete("/model/instance/{instance_id}")
def delete_instance(instance_id: str):
    # TODO: 透传到对应 cluster controller
    return {"result": {}, "status_code": 200, "msg": "Instance deleted"}

@app.put("/model/instance/{instance_id}")
def update_instance(instance_id: str, name: Optional[str] = None, state: Optional[str] = None):
    # TODO: 透传到对应 cluster controller
    return {"result": {}, "status_code": 200, "msg": "Instance updated"}

@app.get("/model/instance/list")
def list_instances():
    # TODO: 聚合所有 cluster 的实例
    return {"result": [], "msg": "success"}

@app.get("/model/instance/{instance_id}")
def get_instance(instance_id: str):
    # TODO: 透传到对应 cluster controller
    return {"result": {}, "msg": "success"}

# ------------------- 生成相关接口 -------------------
@app.post("/generate/completions")
def generate_completions(data: dict):
    # TODO: 透传到指定 cluster/instance
    return {"result": {}, "status_code": 200, "msg": "success"}

@app.post("/generate/chat/completions")
def generate_chat_completions(data: dict):
    # TODO: 透传到指定 cluster/instance
    return {"result": {}, "status_code": 200, "msg": "success"}

# ... 其它 generate/embedding/rerank/similarity/classify 参照上面写

# ------------------- 刷新/同步相关 -------------------
@app.get("/trans/refresh/model")
def refresh_model(cluster_id: str, model_info: str):
    # TODO: 更新本地缓存
    return {"status_code": 200, "msg": "Refreshed"}

# ------------------- 心跳监控线程 -------------------
def heartbeat_monitor():
    while True:
        now = time.time()
        for cid, cluster in list(clusters.items()):
            if now - cluster.last_heartbeat > 120:  # 120秒无心跳
                del clusters[cid]
        time.sleep(60)

def create_center_controller():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=21000)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    return args

args = create_center_controller()

if __name__ == "__main__":
    uvicorn.run(
        "center_controller:app",
        host=args.host,
        port=args.port,
        log_level="info",
        workers=args.workers
    )