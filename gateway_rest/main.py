import os
import time
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

PROCESSOR_URL = os.getenv("PROCESSOR_URL", "http://processor-rest:8000")

app = FastAPI(title="gateway-rest")

REQ = Counter("gateway_requests_total", "Total gateway requests", ["endpoint", "method", "status"])
LAT = Histogram("gateway_latency_seconds", "Gateway latency seconds", ["endpoint", "method"])

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
async def process(payload: ProcessIn):
    endpoint, method = "/process", "POST"
    start = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{PROCESSOR_URL}/process", json=payload.model_dump())

        status = str(r.status_code)
        REQ.labels(endpoint=endpoint, method=method, status=status).inc()
        LAT.labels(endpoint=endpoint, method=method).observe(time.perf_counter() - start)

        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()

    except httpx.RequestError as e:
        REQ.labels(endpoint=endpoint, method=method, status="502").inc()
        LAT.labels(endpoint=endpoint, method=method).observe(time.perf_counter() - start)
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e
