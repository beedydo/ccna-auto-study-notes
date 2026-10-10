"""T40: how requests picks up proxy/CA settings from the environment (trust_env=True, the default).

Run with the lab up, changing only the env vars, e.g.:
  HTTPS_PROXY=http://127.0.0.1:18043 python3 labs/T40/env_proxy_demo.py
"""
import requests

for url in ("http://127.0.0.1:18040/health", "https://127.0.0.1:18044/health"):
    try:
        r = requests.get(url, timeout=(2, 5))
        print(f"{url} -> {r.status_code} {r.text}")
    except requests.exceptions.RequestException as exc:
        print(f"{url} -> {type(exc).__name__}: ...{str(exc)[-112:]}")   # tail holds the real cause
