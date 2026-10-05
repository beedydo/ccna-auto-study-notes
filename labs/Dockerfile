FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git curl openssh-client iputils-ping dnsutils netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /work
CMD ["bash"]
