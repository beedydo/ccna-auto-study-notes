# T27 reference Dockerfile: containerise the T07 mock REST API (labs/T27/mock_api.py).
# Build:  docker build --tag t27-mock-api:1.0 labs/T27
# Run:    docker run --detach --name t27-api --publish 8127:8080 t27-mock-api:1.0
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

LABEL org.opencontainers.image.title="t27-mock-api" \
      org.opencontainers.image.description="Mock network-inventory REST API for the T27 Docker drill"

ENV API_PORT=8080 \
    ACCESS_LOG=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 apiuser \
    && mkdir /data \
    && chown apiuser /data

COPY mock_api.py .

EXPOSE 8080

USER apiuser

ENTRYPOINT ["python3", "mock_api.py"]
CMD ["--host", "0.0.0.0"]
