import httpx
import time

messages = [
    {"role": "system", "content": "You are Mithra (Man Ka Mitra AI), a warm companion. Respond naturally in conversational, colloquial Hindi written ONLY using Latin/English characters (e.g. 'Main samajh sakta hoon dost'). Keep responses concise (around 2 to 4 sentences)."},
    {"role": "user", "content": "Mujhe bahut stress ho raha hai aur kisi se baat karne ka mann nahi hai."}
]

payload = {
    "messages": messages,
    "max_tokens": 65,
    "temperature": 0.7,
    "top_p": 0.9,
    "stream": False
}

t0 = time.time()
print("Sending request to llama-server :8081 directly...", flush=True)
try:
    r = httpx.post("http://127.0.0.1:8081/v1/chat/completions", json=payload, timeout=60.0)
    print(f"Status: {r.status_code} in {time.time()-t0:.2f}s", flush=True)
    data = r.json()
    print("Content:", data["choices"][0]["message"]["content"], flush=True)
except Exception as e:
    print(f"Error after {time.time()-t0:.2f}s:", e, flush=True)
