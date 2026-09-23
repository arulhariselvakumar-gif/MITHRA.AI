import httpx
import time

payload = {
    "message": "मुझे आज बहुत चिंता हो रही है और मैं बहुत परेशान हूँ।",
    "history": [],
    "language": "Hindi"
}

t0 = time.time()
print("Sending Hindi request to FastAPI :8000...", flush=True)
try:
    r = httpx.post("http://127.0.0.1:8000/generate", json=payload, timeout=120.0)
    print(f"Status: {r.status_code} in {time.time()-t0:.2f}s", flush=True)
    print("Response:", r.json(), flush=True)
except Exception as e:
    print("Error:", e, flush=True)
