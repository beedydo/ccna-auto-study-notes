FROM python:3.12-slim
# openssl: self-signed certs in T16/T21/T40/T41 labs; iproute2 + traceroute: ip/ss/traceroute drills in T36/T40
RUN apt-get update && apt-get install -y --no-install-recommends git curl openssh-client iputils-ping dnsutils netcat-openbsd \
        openssl iproute2 traceroute \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# cisco.aci collection for the T19 Ansible playbook
RUN ansible-galaxy collection install cisco.aci
WORKDIR /work
CMD ["bash"]
