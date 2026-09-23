import os
import sys
import time
import subprocess
import httpx
import ctypes

MODEL_PATH = r"C:\Users\anand\models\qwen3-4b-q4_k_m\Qwen3-4B-Q4_K_M.gguf"
SERVER_PATH = r"C:\Users\anand\bin\llama_cpp\llama-server.exe"
HOST = "127.0.0.1"
PORT = 8081
URL = f"http://{HOST}:{PORT}"

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def get_ram_info():
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_gb = round(stat.ullTotalPhys / (1024**3), 2)
        avail_gb = round(stat.ullAvailPhys / (1024**3), 2)
        used_gb = round((stat.ullTotalPhys - stat.ullAvailPhys) / (1024**3), 2)
        return {
            "total_gb": total_gb,
            "used_gb": used_gb,
            "available_gb": avail_gb,
            "percent": stat.dwMemoryLoad,
        }
    except Exception:
        return {"total_gb": 0, "used_gb": 0, "available_gb": 0, "percent": 0}

def main():
    print("=" * 60)
    print("STEP 3 & 4: DIRECT LLAMA-SERVER VERIFICATION & DIRECT INFERENCE")
    print("=" * 60)

    ram_before = get_ram_info()
    print(f"[RAM Before] Used: {ram_before['used_gb']} GB / {ram_before['total_gb']} GB ({ram_before['percent']}%), Available: {ram_before['available_gb']} GB")

    cmd = [
        SERVER_PATH,
        "-m", MODEL_PATH,
        "-c", "2048",
        "-t", "6",
        "--host", HOST,
        "--port", str(PORT),
        "-ngl", "0",
    ]
    print(f"[Command] {' '.join(cmd)}")

    start_time = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    print(f"[Process] Started PID: {proc.pid}. Waiting for server readiness...")

    ready = False
    with httpx.Client(timeout=1.0) as client:
        for attempt in range(60):
            if proc.poll() is not None:
                _, stderr = proc.communicate()
                print(f"[ERROR] Process exited prematurely with code {proc.returncode}!")
                print(f"[STDERR]\n{stderr}")
                sys.exit(1)
            try:
                r = client.get(f"{URL}/health")
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.5)

    if not ready:
        print("[ERROR] Timed out waiting for llama-server readiness!")
        proc.terminate()
        sys.exit(1)

    startup_duration = time.perf_counter() - start_time
    print(f"[SUCCESS] llama-server ready in {startup_duration:.2f} seconds!")

    ram_after_load = get_ram_info()
    print(f"[RAM After Load] Used: {ram_after_load['used_gb']} GB ({ram_after_load['percent']}%), Available: {ram_after_load['available_gb']} GB")
    ram_diff_load = round(ram_after_load['used_gb'] - ram_before['used_gb'], 2)
    print(f"[RAM Delta for Model Load] +{ram_diff_load} GB")

    print("\n" + "=" * 60)
    print("STEP 4: DIRECT CHAT INFERENCE REQUEST TO LLAMA-SERVER")
    print("=" * 60)

    prompt_payload = {
        "messages": [
            {"role": "system", "content": "You are Mithra, a supportive and empathetic AI companion."},
            {"role": "user", "content": "Hello Mithra! Tell me in one or two sentences how to handle feeling overwhelmed today."}
        ],
        "temperature": 0.7,
        "max_tokens": 128,
        "stream": False,
    }

    t0 = time.perf_counter()
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(f"{URL}/v1/chat/completions", json=prompt_payload)
    inf_duration = time.perf_counter() - t0

    ram_during_inf = get_ram_info()
    print(f"[RAM During Inference] Used: {ram_during_inf['used_gb']} GB ({ram_during_inf['percent']}%), Available: {ram_during_inf['available_gb']} GB")

    if resp.status_code != 200:
        print(f"[ERROR] Chat completions failed with HTTP {resp.status_code}: {resp.text}")
        proc.terminate()
        sys.exit(1)

    data = resp.json()
    reply = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    completion_tokens = usage.get("completion_tokens", 0)
    prompt_tokens = usage.get("prompt_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    tok_per_sec = round(completion_tokens / inf_duration, 2) if inf_duration > 0 and completion_tokens > 0 else 0

    print(f"[HTTP Status] {resp.status_code}")
    print(f"[Total Inference Time] {inf_duration:.2f} s")
    print(f"[Prompt Tokens] {prompt_tokens}")
    print(f"[Completion Tokens] {completion_tokens}")
    print(f"[Total Tokens] {total_tokens}")
    print(f"[Speed] {tok_per_sec} tokens/sec")
    print("\n[DIRECT QWEN GENERATED REPLY]:")
    print("-" * 40)
    print(reply)
    print("-" * 40)

    print("\n[SHUTDOWN] Terminating test llama-server...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
        print("[SHUTDOWN] llama-server stopped cleanly.")
    except subprocess.TimeoutExpired:
        proc.kill()
        print("[SHUTDOWN] llama-server force killed.")

    print("\n" + "=" * 60)
    print("STEP 3 & 4 COMPLETE: REAL QWEN3-4B INFERENCE CONFIRMED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
