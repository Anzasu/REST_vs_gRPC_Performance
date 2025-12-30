FROM python:3.12-slim
WORKDIR /app

COPY processor_grpc/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY proto /proto
RUN python -m grpc_tools.protoc -I/proto \
    --python_out=/app --grpc_python_out=/app /proto/processor.proto

COPY processor_grpc/ .
EXPOSE 50051 9102
CMD ["python", "server.py"]
