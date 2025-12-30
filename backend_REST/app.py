import time
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="backend_REST", version="1.0.0")

# --- Prometheus Metrics ---
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

PROCESS_DURATION_SECONDS = Histogram(
    "process_duration_seconds",
    "Duration of /process business logic in seconds",
)

# --- Request Model ---
class ProcessRequest(BaseModel):
    value: int
    delay_ms: Optional[int] = 0

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/process")
def process(payload: ProcessRequest):
    start = time.perf_counter()

    delay_ms = payload.delay_ms or 0
    if delay_ms > 0:
        time.sleep(delay_ms / 1000.0)

    result = payload.value * 2
    PROCESS_DURATION_SECONDS.observe(time.perf_counter() - start)

    return {"input": payload.value, "result": result, "delay_ms": delay_ms, "backend": "REST"}

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return PlainTextResponse(content=data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
