import os
import time
from concurrent import futures

import grpc
from prometheus_client import Counter, Histogram, start_http_server

import processor_pb2
import processor_pb2_grpc

REQ = Counter("processor_grpc_requests_total", "Total gRPC processor requests", ["status"])
LAT = Histogram("processor_grpc_latency_seconds", "gRPC processor latency seconds")


class ProcessorServicer(processor_pb2_grpc.ProcessorServicer):
    def Process(self, request, context):
        start = time.perf_counter()
        try:
            if request.delay_ms > 0:
                time.sleep(request.delay_ms / 1000)

            result = int(request.value) * 2

            REQ.labels(status="OK").inc()
            LAT.observe(time.perf_counter() - start)

            return processor_pb2.ProcessReply(result=result, delay_ms=int(request.delay_ms))
        except Exception:
            REQ.labels(status="ERR").inc()
            LAT.observe(time.perf_counter() - start)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("internal error")
            return processor_pb2.ProcessReply()


def serve():
    metrics_port = int(os.getenv("METRICS_PORT", "9102"))
    start_http_server(metrics_port)

    grpc_port = int(os.getenv("GRPC_PORT", "50051"))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    processor_pb2_grpc.add_ProcessorServicer_to_server(ProcessorServicer(), server)
    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()

    print(f"processor-grpc listening on :{grpc_port}, metrics on :{metrics_port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
