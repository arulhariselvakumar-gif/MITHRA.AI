import httpx
import time

try:
    r = httpx.get("http://127.0.0.1:8081/health", timeout=5.0)
    print("LLAMA HEALTH:", r.status_code, r.text)
except Exception as e:
    print("LLAMA HEALTH ERROR:", e)

try:
    r = httpx.get("http://127.0.0.1:8000/health", timeout=5.0)
    print("FASTAPI HEALTH:", r.status_code, r.text)
except Exception as e:
    print("FASTAPI HEALTH ERROR:", e)
