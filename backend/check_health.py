import httpx
try:
    r = httpx.get("http://127.0.0.1:4000/api/health", timeout=3.0)
    print("EXPRESS:", r.status_code, r.text, flush=True)
except Exception as e:
    print("EXPRESS ERROR:", e, flush=True)

try:
    r = httpx.get("http://127.0.0.1:8000/health", timeout=3.0)
    print("FASTAPI:", r.status_code, r.text, flush=True)
except Exception as e:
    print("FASTAPI ERROR:", e, flush=True)
