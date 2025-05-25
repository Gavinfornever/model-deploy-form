"""
A controller manages distributed workers.
It sends worker addresses to clients.
"""
import argparse
import asyncio
from calendar import c
import dataclasses
from enum import Enum, auto
import json
import logging
import os
import time
from typing import List, Union
import threading

from fastapi import FastAPI, Request, status, Depends
from fastapi.responses import StreamingResponse,JSONResponse
import numpy as np
import requests
import uvicorn
import random
from utils import build_logger, ErrorCode, WorkerInfo, DaemonInfo
from config import config
import redis
from pymongo import MongoClient

from dataclasses import asdict

import ray
import subprocess

CONTROLLER_HEART_BEAT_EXPIRATION = 90
WORKER_API_TIMEOUT = 100
SERVER_ERROR_MSG = (
    "**NETWORK ERROR DUE TO HIGH TRAFFIC. PLEASE REGENERATE OR REFRESH THIS PAGE.**"
)

# rds = redis.Redis(host=config['REDIS']['host'],port=int(config['REDIS']['port']),password=config['REDIS']['password'])
rds = None
logger = None
cluster_controller = None
mongo_db = None
daemon_info_key = "daemon_info"
worker_info_key = "worker_info"

class DispatchMethod(Enum):
    LOTTERY = auto()
    SHORTEST_QUEUE = auto()

    @classmethod
    def from_str(cls, name):
        if name == "lottery":
            return cls.LOTTERY
        elif name == "shortest_queue":
            return cls.SHORTEST_QUEUE
        else:
            raise ValueError(f"Invalid dispatch method")




def heart_beat_controller(cluster_controller):
    while True:
        time.sleep(CONTROLLER_HEART_BEAT_EXPIRATION)
        worker_info = rds.get(worker_info_key)
        daemon_info = rds.get(daemon_info_key)
        if worker_info:
            cluster_controller.worker_info = deserialize(worker_info)
        if daemon_info:
            cluster_controller.daemon_info = daemon_deserialize(daemon_info)
        logger.info("check heart beat")
        cluster_controller.remove_stale_workers_by_expiration()
        # time.sleep(CONTROLLER_HEART_BEAT_EXPIRATION)


def serialize(worker_info):
    res = {key: worker.to_str() for key, worker in worker_info.items()}
    return json.dumps(res)

def deserialize(worker_info):
    worker_info = json.loads(worker_info)
    return {key: WorkerInfo.from_str(worker) for key, worker in worker_info.items()}

def daemon_serialize(daemon_info):
    res = {key: d.to_dict() for key, d in daemon_info.items()}
    return json.dumps(res)

def daemon_deserialize(daemon_info):
    daemon_info = json.loads(daemon_info)
    return {key: DaemonInfo.from_dict(d) for key, d in daemon_info.items()}

class ClusterController:
    def __init__(self, dispatch_method: str):
        # Dict[str -> WorkerInfo]
        self.worker_info = {}
        self.daemon_info = {}
        self.dispatch_method = DispatchMethod.from_str(dispatch_method)

        self.heart_beat_thread = threading.Thread(
            target=heart_beat_controller, args=(self,)
        )
        self.heart_beat_thread.start()

    def register_worker(
        self, worker_name: str, check_heart_beat: bool, worker_status: dict
    ):
        if worker_name not in self.worker_info:
            logger.info(f"Register a new worker: {worker_name}")
        else:
            logger.info(f"Register an existing worker: {worker_name}")

        if not worker_status:
            worker_status = self.get_worker_status(worker_name)
        if not worker_status:
            return False

        self.worker_info[worker_name] = WorkerInfo(
            worker_status["model_names"],
            worker_status["speed"],
            worker_status["queue_length"],
            check_heart_beat,
            time.time(),
            extend_info=worker_status,
        )
        # 持久化更新到 Redis
        rds.set(worker_info_key, serialize(self.worker_info))
        logger.info(f"Register done: {worker_name}, {worker_status}")
        return True

    def get_worker_status(self, worker_name: str):
        try:
            r = requests.post(worker_name + "/worker_get_status", timeout=5)
        except requests.exceptions.RequestException as e:
            logger.error(f"Get status fails: {worker_name}, {e}")
            return None

        if r.status_code != 200:
            logger.error(f"Get status fails: {worker_name}, {r}")
            return None

        return r.json()

    def remove_worker(self, worker_name: str):
        logger.info("remove worker")
        del self.worker_info[worker_name]
        rds.set(worker_info_key, serialize(self.worker_info))

    # def refresh_all_workers(self):
    #     old_info = dict(self.worker_info)
    #     self.worker_info = {}
    #     for w_name, w_info in old_info.items():
    #         if not self.register_worker(w_name, w_info.check_heart_beat, None):
    #             logger.info(f"Remove stale worker: {w_name}")
    #     rds.set(worker_info_key, serialize(self.worker_info))


    def list_models(self):
        models = dict()

        for w_name, w_info in self.worker_info.items():
            for name in w_info.model_names:
                if name not in models:
                    models[name] = {'worker_num': 0}
                models[name]['worker_num'] += 1
                models[name][models[name]['worker_num']] = w_info

        return models

    def get_worker_address(self, model_name: str):
        if self.dispatch_method == DispatchMethod.LOTTERY:
            worker_names = []
            worker_speeds = []
            for w_name, w_info in self.worker_info.items():
                if model_name in w_info.model_names:
                    worker_names.append(w_name)
                    worker_speeds.append(w_info.speed)
            worker_speeds = np.array(worker_speeds, dtype=np.float32)
            norm = np.sum(worker_speeds)
            if norm < 1e-4:
                return ""
            worker_speeds = worker_speeds / norm
            if True:  # Directly return address
                pt = np.random.choice(np.arange(len(worker_names)), p=worker_speeds)
                worker_name = worker_names[pt]
                return worker_name

            # Check status before returning
            while True:
                pt = np.random.choice(np.arange(len(worker_names)), p=worker_speeds)
                worker_name = worker_names[pt]

                if self.get_worker_status(worker_name):
                    break
                else:
                    self.remove_worker(worker_name)
                    worker_speeds[pt] = 0
                    norm = np.sum(worker_speeds)
                    if norm < 1e-4:
                        return ""
                    worker_speeds = worker_speeds / norm
                    continue
            return worker_name
        elif self.dispatch_method == DispatchMethod.SHORTEST_QUEUE:
            worker_names = []
            worker_qlen = []
            for w_name, w_info in self.worker_info.items():
                if model_name in w_info.model_names:
                    worker_names.append(w_name)
                    worker_qlen.append(w_info.queue_length / w_info.speed)
            if len(worker_names) == 0:
                return ""
            min_index = np.argmin(worker_qlen)
            w_name = worker_names[min_index]
            self.worker_info[w_name].queue_length += 1
            logger.info(
                f"names: {worker_names}, queue_lens: {worker_qlen}, ret: {w_name}"
            )
            rds.set(worker_info_key, serialize(cluster_controller.worker_info))
            return w_name
        else:
            raise ValueError(f"Invalid dispatch method: {self.dispatch_method}")

    def receive_heart_beat(self, worker_name: str, queue_length: int):
        if worker_name not in self.worker_info:
            logger.info(f"Receive unknown heart beat. {worker_name}")
            return False

        self.worker_info[worker_name].queue_length = queue_length
        self.worker_info[worker_name].last_heart_beat = time.time()
        
        rds.set(worker_info_key, serialize(self.worker_info))
        logger.info(f"Receive heart beat. {worker_name}")
        return True

    def remove_stale_workers_by_expiration(self):
        expire = time.time() - CONTROLLER_HEART_BEAT_EXPIRATION
        to_delete = []
        for worker_name, w_info in self.worker_info.items():
            if w_info.check_heart_beat and w_info.last_heart_beat < expire:
                logger.info("time out, geting worker status")
                r = self.get_worker_status(worker_name)
                if r is None:
                    logger.info("model not exist")
                    to_delete.append(worker_name)
                else:
                    self.worker_info[worker_name].last_heart_beat = time.time()
                    rds.set(worker_info_key, serialize(self.worker_info))
                    logger.info(f"model exists , change last heart beat{worker_name}")
        for worker_name in to_delete:
            self.remove_worker(worker_name)

    def handle_no_worker(self, params):
        logger.info(f"no worker: {params['model']}")
        ret = {
            "text": SERVER_ERROR_MSG,
            "error_code": ErrorCode.CONTROLLER_NO_WORKER,
        }
        return json.dumps(ret).encode() + b"\0"

    def handle_worker_timeout(self, worker_address):
        logger.info(f"worker timeout: {worker_address}")
        ret = {
            "text": SERVER_ERROR_MSG,
            "error_code": ErrorCode.CONTROLLER_WORKER_TIMEOUT,
        }
        return json.dumps(ret).encode() + b"\0"

    # Let the controller act as a worker to achieve hierarchical
    # management. This can be used to connect isolated sub networks.
    def worker_api_get_status(self):
        model_names = set()
        speed = 0
        queue_length = 0

        for w_name in self.worker_info:
            worker_status = self.get_worker_status(w_name)
            if worker_status is not None:
                model_names.update(worker_status["model_names"])
                speed += worker_status["speed"]
                queue_length += worker_status["queue_length"]

        model_names = sorted(list(model_names))
        return {
            "model_names": model_names,
            "speed": speed,
            "queue_length": queue_length,
        }

    def worker_api_generate_stream(self, params):
        worker_addr = self.get_worker_address(params["model"])
        if not worker_addr:
            yield self.handle_no_worker(params)

        try:
            response = requests.post(
                worker_addr + "/worker_generate_stream",
                json=params,
                stream=True,
                timeout=WORKER_API_TIMEOUT,
            )
            for chunk in response.iter_lines(decode_unicode=False, delimiter=b"\0"):
                if chunk:
                    yield chunk + b"\0"
        except requests.exceptions.RequestException as e:
            yield self.handle_worker_timeout(worker_addr)
    
    def register_daemon(
        self, data: dict
    ):
        # 若不添加进程间共享，则每个worker进程都会注册一次，需要解决
        daemon_id = data.get('daemon_id', data.get('daemon_IP'))
        flag = True
        if daemon_id not in self.daemon_info:
            logger.info(f"Register done: {data.get('daemon_name')}, {data.get('daemon_IP')}")
        else:
            logger.info("Daemon exists!")
            flag = False
        self.daemon_info[daemon_id] = DaemonInfo(**data)
        t = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        data['time'] = t
        mongo_db.daemon_info.insert_one(data)
        return flag
      
    def list_daemons(self):
        invalid_daemons=[]
        for key, info in self.daemon_info.items():
            daemon_heartbeat=f"http://{info.daemon_IP}:{info.daemon_port}/heartbeat"
            try:
                requests.get(daemon_heartbeat,timeout=5)
            except Exception:
                invalid_daemons.append(key)
        for k in invalid_daemons:
            del self.daemon_info[k]
        return {key: d.to_dict() for key, d in self.daemon_info.items()}

app = FastAPI()

@app.middleware("http")
async def get_info_from_redis(request: Request, call_next):
    # 请求前 获取redis信息
    worker_info = rds.get(worker_info_key)
    daemon_info = rds.get(daemon_info_key)
    if worker_info:
        cluster_controller.worker_info = deserialize(worker_info)
    if daemon_info:
        cluster_controller.daemon_info = daemon_deserialize(daemon_info)
    response = await call_next(request)
    # 请求后 存入更改过的信息到redis
    # if controller.worker_info is not None:
    #     rds.set(worker_info_key, serialize(controller.worker_info))
    rds.set(daemon_info_key, daemon_serialize(cluster_controller.daemon_info))
    return response

@app.post("/register_daemon")
async def register_daemon(request: Request):
    data = await request.json()
    if cluster_controller.register_daemon(data):
        return status.HTTP_200_OK
    return status.HTTP_208_ALREADY_REPORTED

@app.post("/list_daemons")
async def list_daemons():
    machines = cluster_controller.list_daemons()
    return JSONResponse(content={"machines": machines},status_code=200)

@app.post("/register_worker")
async def register_worker(request: Request):
    data = await request.json()
    cluster_controller.register_worker(
        data["worker_name"], data["check_heart_beat"], data.get("worker_status", None)
    )


@app.post("/refresh_all_workers")
async def refresh_all_workers():
    models = cluster_controller.refresh_all_workers()


@app.post("/list_models")
async def list_models():
    models = cluster_controller.list_models()
    return {"models": models}


@app.post("/get_worker_address")
async def get_worker_address(request: Request):
    data = await request.json()
    addr = cluster_controller.get_worker_address(data["model"])
    return {"address": addr}


@app.post("/receive_heart_beat")
async def receive_heart_beat(request: Request):
    data = await request.json()
    exist = cluster_controller.receive_heart_beat(data["worker_name"], data["queue_length"])
    return {"exist": exist}


@app.post("/worker_generate_stream")
async def worker_api_generate_stream(request: Request):
    params = await request.json()
    generator = cluster_controller.worker_api_generate_stream(params)
    return StreamingResponse(generator)


@app.post("/worker_get_status")
async def worker_api_get_status(request: Request):
    return cluster_controller.worker_api_get_status()


@app.get("/test_connection")
async def worker_api_get_status(request: Request):
    return "success"

@ray.remote
def launch_vllm_worker():
    cmd = [
        "CUDA_VISIBLE_DEVICES=0",
        "python", "/root/fschat_deploy/fschat/vllm_worker.py",
        "--host", "0.0.0.0",
        "--port", "20999",
        "--model-path", "/root/models/Qwen2.5-0.5B",
        "--trust-remote-code",
        "--controller-address", "http://localhost:20091",
        "--worker-address", "http://localhost:20999",
        "--model-names", "qwen2.5-0.5b_vllm",
        "--log-dir", "/root/fschat_deploy/logs",
        "--gpus", "0",
        "--gpu-memory-utilization", "0.3"
    ]
    # Join command for shell execution
    full_cmd = " ".join(cmd)
    process = subprocess.Popen(full_cmd, shell=True)
    process.wait()

from utils import DeployCommand
@app.post("/deploy")
async def deploy_model(params: DeployCommand):
    try:
        print(params)
        try:
            launch_vllm_worker.remote()
        except Exception as e:
            return create_error_response(ErrorCode.INTERNAL_ERROR,str(e))
    except Exception as e:
        raise HTTPException(500,str(e))

def create_cluster_controller():
    # Make sure Ray is initialized
    if not ray.is_initialized():
        ray.init(address='auto')  # or ray.init() for local

    global logger
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=21001)
    parser.add_argument("--log-path", type=str, required=True)
    parser.add_argument("--worker",type=int,default=4)
    parser.add_argument("--redis_host",type=str, default="localhost")
    parser.add_argument("--redis_port",type=str, default="6379")
    parser.add_argument("--redis_passwd",type=str, default="")
    parser.add_argument("--redis_key",type=str, default="fschat")

    parser.add_argument("--mongo_host",type=str, default="localhost")
    parser.add_argument("--mongo_port",type=str, default="27017")
    parser.add_argument("--mongo_passwd",type=str, default="650803")
    parser.add_argument("--mongo_user",type=str, default="root")

    parser.add_argument(
        "--dispatch-method",
        type=str,
        choices=["lottery", "shortest_queue"],
        default="shortest_queue",
    )
    parser.add_argument(
        "--ssl",
        action="store_true",
        required=False,
        default=False,
        help="Enable SSL. Requires OS Environment variables 'SSL_KEYFILE' and 'SSL_CERTFILE'.",
    )
    args = parser.parse_args()
    logger = build_logger("cluster_controller", "cluster_controller.log", args.log_path)
    logger.info(f"args: {args}")
    cluster_controller = ClusterController(args.dispatch_method)

    rds = redis.Redis(host=args.redis_host,port=int(args.redis_port),password=args.redis_passwd)

    connection_string = f"mongodb://{args.mongo_user}:{args.mongo_passwd}@{args.mongo_host}:{args.mongo_port}/?authSource=admin"
    mongo_client = MongoClient(connection_string)
    mongo_db = mongo_client.fschat
    

    global worker_info_key
    global daemon_info_key
    worker_info_key = worker_info_key + "_" + args.redis_key
    daemon_info_key = daemon_info_key + "_" + args.redis_key
    rds.delete(worker_info_key)
    rds.delete(daemon_info_key)

    worker_info = rds.get(worker_info_key)
    if worker_info:
        cluster_controller.worker_info = deserialize(worker_info)
    daemon_info = rds.get(daemon_info_key)
    if daemon_info:
        cluster_controller.daemon_info = daemon_deserialize(daemon_info)

    return args, cluster_controller, rds, worker_info_key, daemon_info_key, mongo_db

args, cluster_controller, rds, worker_info_key, daemon_info_key, mongo_db = create_cluster_controller()



if __name__ == "__main__":
    # 清理redis缓存
    uvicorn.run("cluster_controller:app", host=args.host, port=args.port, log_level="info", workers=args.worker)
