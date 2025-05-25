"""
A model worker that executes the model based on vLLM.

See documentations at docs/vllm_integration.md
"""

import argparse
import asyncio
import json
import uuid
from typing import List
import os
from datetime import datetime
import setproctitle

from fastapi import FastAPI, Request, BackgroundTasks, Response
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
from vllm import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.sampling_params import SamplingParams
from vllm.utils import random_uuid
import threading
from base_model_worker import BaseModelWorker
from utils import get_context_length, build_logger


app = FastAPI()
acquire_timeout = None
class VLLMWorker(BaseModelWorker):
    def __init__(
        self,
        controller_addr: str,
        worker_addr: str,
        worker_id: str,
        model_path: str,
        model_names: List[str],
        limit_worker_concurrency: int,
        no_register: bool,
        llm_engine: AsyncLLMEngine,
        conv_template: str,
        worker_info,
    ):
        global logger
        super().__init__(
            logger,
            controller_addr,
            worker_addr,
            worker_id,
            model_path,
            model_names,
            limit_worker_concurrency,
            conv_template,
        )
        self.info = worker_info
        logger.info(
            f"Loading the model {self.model_names} on worker {worker_id}, worker type: vLLM worker..."
        )
        self.tokenizer = llm_engine.engine.tokenizer
        self.context_len = get_context_length(llm_engine.engine.model_config.hf_config)

        if not no_register:
            self.init_heart_beat()

    async def generate_stream(self, params):
        self.call_ct += 1

        context = params.pop("prompt")
        if self.template:
            context = self.template.format(context)
        request_id = params.pop("request_id")
        sampling_params = SamplingParams(**params)
        logger.info(f"context: {context}, sampling_params: {sampling_params}")
        results_generator = engine.generate(context, sampling_params, request_id)

        async for request_output in results_generator:
            prompt = request_output.prompt
            text_outputs = [output.text for output in request_output.outputs]
            prompt_tokens = len(request_output.prompt_token_ids)
            completion_tokens = sum(
                len(output.token_ids) for output in request_output.outputs
            )
            ret = {
                "text": text_outputs,
                "error_code": 0,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                "cumulative_logprob": [
                    output.cumulative_logprob for output in request_output.outputs
                ],
                "finish_reason": request_output.outputs[0].finish_reason
                if len(request_output.outputs) == 1
                else [output.finish_reason for output in request_output.outputs],
            }
            yield (json.dumps(ret) + "\0").encode()

    async def generate_stream_v2(self, params):
        self.call_ct += 1

        context = params.pop("prompt")
        # 添加类型检查和转换
        if not isinstance(context, str):
            if isinstance(context, list) and len(context) > 0:
                context = context[0]
                if not isinstance(context, str):
                    raise TypeError(f"Prompt must be a string, got {type(context)}")
            else:
                raise TypeError(f"Prompt must be a string, got {type(context)}")
        
        if self.template:
            context = self.template.format(context)
        request_id = params.pop("request_id")
        sampling_params = SamplingParams(**params)
        logger.info(f"context: {context}, sampling_params: {sampling_params}")
        results_generator = engine.generate(context, sampling_params, request_id)

        last_output = ""
        async for request_output in results_generator:    
            text_outputs = request_output.outputs[-1].text
            text_outputs_stream = text_outputs[len(last_output):]
            last_output = text_outputs
            prompt_tokens = len(request_output.prompt_token_ids)
            completion_tokens = sum(
                len(output.token_ids) for output in request_output.outputs
            )
            ret = {
                "text": text_outputs_stream,
                "error_code": 0,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                "cumulative_logprob": [
                    output.cumulative_logprob for output in request_output.outputs
                ],
                "finish_reason": request_output.outputs[0].finish_reason
                if len(request_output.outputs) == 1
                else [output.finish_reason for output in request_output.outputs],
            }
            yield (json.dumps(ret) + "\0").encode()


    async def generate(self, params):
        async for x in self.generate_stream(params):
            pass
        return json.loads(x[:-1].decode())
    
    def get_status(self):
        dicts = super().get_status()
        dicts.update(self.info)
        return dicts


def release_worker_semaphore():
    worker.semaphore.release()


def acquire_worker_semaphore():
    if worker.semaphore is None:
        worker.semaphore = asyncio.Semaphore(worker.limit_worker_concurrency)
    return worker.semaphore.acquire()


def create_background_tasks(request_id):
    async def abort_request() -> None:
        await engine.abort(request_id)

    background_tasks = BackgroundTasks()
    background_tasks.add_task(release_worker_semaphore)
    background_tasks.add_task(abort_request)
    return background_tasks


@app.post("/worker_generate_stream")
async def api_generate_stream(request: Request):
    semaphore = None
    request_id = random_uuid()
    params = await request.json()
    params["request_id"] = request_id
    try:
        semaphore = await asyncio.wait_for(acquire_worker_semaphore(),acquire_timeout)
        if not semaphore: 
            return StreamingResponse(content="Too Many Requests!", status_code=503, headers={"Content-Type":"text/event-stream"})
        generator = worker.generate_stream_v2(params)
    except asyncio.TimeoutError:
        return StreamingResponse(content="Too Many Requests, acquire_worker_semaphore Timeout!", status_code=503, headers={"Content-Type":"text/event-stream"})
    except Exception as e:
        return StreamingResponse(content=f"Error: {e}", status_code=500)
    finally:
        background_tasks = create_background_tasks(request_id)
        if semaphore:
            return StreamingResponse(generator, background=background_tasks)
    return StreamingResponse(generator, background=background_tasks)


@app.post("/worker_generate")
async def api_generate(request: Request):
    semaphore = None
    params = await request.json()
    request_id = random_uuid()
    params["request_id"] = request_id
    try:
        semaphore = await asyncio.wait_for(acquire_worker_semaphore(),acquire_timeout)
        if not semaphore: 
            return JSONResponse(content="Too Many Requests!", status_code=503)
        output = await worker.generate(params)
    except asyncio.TimeoutError:
        return JSONResponse(content="Too Many Requests, acquire_worker_semaphore Timeout!", status_code=503)
    except Exception as e:
        return JSONResponse(content=f"Error: {e}", status_code=500)
    finally:
        if semaphore:
            release_worker_semaphore()
        await engine.abort(request_id)
    return JSONResponse(output)


@app.post("/worker_get_status")
async def api_get_status(request: Request):
    return worker.get_status()


@app.post("/count_token")
async def api_count_token(request: Request):
    params = await request.json()
    return worker.count_token(params)


@app.post("/worker_get_conv_template")
async def api_get_conv(request: Request):
    return worker.get_conv_template()


@app.post("/model_details")
async def api_model_details(request: Request):
    return {"context_length": worker.context_len}

@app.post("/shutdown")
def shutdown():
    try:
        os.kill(os.getpid(), 9)
        return 1
    except Exception as e:
        return str(e)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=21002)
    parser.add_argument("--worker-address", type=str, default="http://localhost:21002")
    parser.add_argument("--log-dir", type=str, required=True)
    parser.add_argument(
        "--controller-address", type=str, default="http://localhost:21001"
    )
    parser.add_argument("--model-path", type=str, default="lmsys/vicuna-7b-v1.5")
    parser.add_argument(
        "--model-names",
        type=lambda s: s.split(","),
        help="Optional display comma separated names",
    )
    parser.add_argument("--limit-worker-concurrency", type=int, default=1024)
    parser.add_argument("--acquire-timeout", type=int, default=10)
    parser.add_argument("--no-register", action="store_true")
    parser.add_argument("--gpus", type=str, required=True)
    parser.add_argument(
        "--conv-template", type=str, default=None, help="Conversation prompt template."
    )
    parser.add_argument("--docker-name", type=str, default="")

    parser = AsyncEngineArgs.add_cli_args(parser)
    args = parser.parse_args()

    if args.model_path:
        args.model = args.model_path
    if args.gpus:
        args.tensor_parallel_size = len(args.gpus.split(","))

    acquire_timeout = args.acquire_timeout
        
    worker_id = str(uuid.uuid4())[:8]
    time=datetime.now().strftime('%Y%m%d%H%M%S')
    logger = build_logger("vllm_worker", f"{args.model_names[0]}_{time}.log", args.log_dir)

    engine_args = AsyncEngineArgs.from_cli_args(args)
    engine = AsyncLLMEngine.from_engine_args(engine_args)

    worker_info = {"docker_name": args.docker_name, "host": args.host, "port": args.port, "worker-address": args.worker_address, "model-path": args.model_path,
                   "template": args.conv_template, "gpus": args.gpus, "start_type": "vllm", "vllm_args": engine_args.__dict__}
    
    worker = VLLMWorker(
        args.controller_address,
        args.worker_address,
        worker_id,
        args.model_path,
        args.model_names,
        args.limit_worker_concurrency,
        args.no_register,
        engine,
        args.conv_template,
        worker_info,
    )
    setproctitle.setproctitle(args.model_names[0]+"_deploy_model")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    import torch.distributed as dist
    if dist.is_available() and dist.is_initialized():
        dist.destroy_process_group()
