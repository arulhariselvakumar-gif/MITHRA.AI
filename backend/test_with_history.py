import httpx
import time

payload = {
    "message": "Mujhe bahut stress ho raha hai aur kisi se baat karne ka mann nahi hai.",
    "history": [
        {"role": "user", "message": "मुझे आज बहुत चिंता हो रही है और मैं बहुत परेशान हूँ।"},
        {"role": "assistant", "message": "मेरा आपके बारे में खुशी है कि आप बात कर रहे हैं।"}
    ],
    "language": "Hinglish"
}

t0 = time.time()
print("Sending Hinglish with history to FastAPI :8000...", flush=True)
try:
    r = httpx.post("http://127.0.0.1:8000/generate", json=payload, timeout=60.0)
    print(f"Status: {r.status_code} in {time.time()-t0:.2f}s", flush=True)
    print("Response:", r.json(), flush=True)
except Exception as e:
    print(f"Error after {time.time()-t0:.2f}s:", e, flush=True)
