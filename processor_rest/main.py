import time
from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI(title="processor-rest")

REQ = Counter("processor_requests_total", "Total processor requests", ["endpoint", "method", "status"])
LAT = Histogram("processor_latency_seconds", "Processor latency seconds", ["endpoint", "method"])


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
    endpoint, method = "/process", "POST"
    start = time.perf_counter()

    if payload.delay_ms > 0:
        time.sleep(payload.delay_ms / 1000)

    result = payload.value * 2

    LAT.labels(endpoint=endpoint, method=method).observe(time.perf_counter() - start)
    REQ.labels(endpoint=endpoint, method=method, status="200").inc()

    return {"result": result, "delay_ms": payload.delay_ms}
