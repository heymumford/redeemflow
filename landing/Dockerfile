FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    fastapi uvicorn[standard] httpx \
    opentelemetry-api opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-http \
    opentelemetry-instrumentation-fastapi
COPY server.py .
COPY index.html .
COPY VERSION .
COPY img/ img/
EXPOSE 8080
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--access-log"]
