import os
import time
import grpc

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

import processor_pb2
import processor_pb2_grpc

PROCESSOR_ADDR = os.getenv("PROCESSOR_GRPC_ADDR", "processor-grpc:50051")

app = FastAPI(title="gateway-grpc")

REQ = Counter("gateway_grpc_requests_total", "Total gateway grpc requests", ["status"])
LAT = Histogram("gateway_grpc_latency_seconds", "Gateway grpc latency seconds")


class ProcessIn(BaseModel):
    value: int
    delay_ms: int = 0


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/process")
def process(payload: ProcessIn):
    start = time.perf_counter()
    try:
        with grpc.insecure_channel(PROCESSOR_ADDR) as channel:
            stub = processor_pb2_grpc.ProcessorStub(channel)
            resp = stub.Process(
                processor_pb2.ProcessRequest(value=payload.value, delay_ms=payload.delay_ms),
                timeout=5.0,
            )

        REQ.labels(status="200").inc()
        LAT.observe(time.perf_counter() - start)
        return {"result": resp.result, "delay_ms": resp.delay_ms}

    except grpc.RpcError as e:
        REQ.labels(status="502").inc()
        LAT.observe(time.perf_counter() - start)
        raise HTTPException(status_code=502, detail=f"Upstream gRPC error: {e.code()} {e.details()}") from e
