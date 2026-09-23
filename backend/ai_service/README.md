# Mithra AI Microservice (Real Qwen3-4B GGUF)

Dedicated Python FastAPI AI microservice powering Mithra with the real **Qwen3-4B GGUF** model using **llama.cpp** on local CPU (Windows 11).

---

## Architecture Overview

```text
Frontend (Vanilla HTML/JS)
         ↓
Express Backend (:4000)
         ↓
FastAPI AI Service (:8000)
         ↓
QwenModelService (Python)
         ↓
llama-server (:8081)
         ↓
Qwen3-4B-Q4_K_M.gguf
         ↓
Intel Core i5-12450H (CPU Only)
```

- **Inference Engine**: `llama-server.exe` running locally on `127.0.0.1:8081` with AVX2 CPU acceleration and 6 threads.
- **Model Quantization**: `Q4_K_M` (~2.33 GB file size), optimized for 16 GB RAM laptops.
- **Safety**: Deterministic emergency/distress guardrail (Tele-MANAS `14416` and National Emergency `112`) runs before LLM generation.
- **Thinking Mode**: Internal reasoning (`<think>...</think>`) tags are automatically filtered out before returning responses.

---

## File Locations (Outside Git)

- **Model File**: `C:\Users\anand\models\qwen3-4b-q4_k_m\Qwen3-4B-Q4_K_M.gguf`
- **Inference Server**: `C:\Users\anand\bin\llama_cpp\llama-server.exe`

*(These large files remain outside the git repository to prevent repository bloat).*

---

## 1. Environment Configuration

The service is configured via `.env` in `backend/ai_service/.env`:

```env
MODEL_NAME=Qwen3-4B
MODEL_PATH=C:\Users\anand\models\qwen3-4b-q4_k_m\Qwen3-4B-Q4_K_M.gguf
LLAMA_SERVER_PATH=C:\Users\anand\bin\llama_cpp\llama-server.exe
LLAMA_PORT=8081
LLAMA_HOST=127.0.0.1
CPU_THREADS=6
CONTEXT_SIZE=2048
MAX_TOKENS=512
DEVICE=cpu
DEMO_MODE=false
```

---

## 2. Starting the Service

From PowerShell in `backend/ai_service`:

```powershell
# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Start FastAPI (which automatically manages the internal llama-server)
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

FastAPI will start, verify the local model file, start `llama-server.exe` on port 8081, verify real token generation, and switch to `mode: "live"`.

---

## 3. Testing the Endpoints

### Health Check (`GET /health`)

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method GET
```

**Expected Live Response:**
```json
{
  "status": "ok",
  "model": "Qwen3-4B",
  "mode": "live"
}
```

---

### Emotional Support Generation (`POST /generate`)

```powershell
$body = @{
    message  = "I have been feeling extremely stressed about everything lately."
    history  = @()
    language = "English"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/generate" -Method POST -ContentType "application/json" -Body $body
```

**Expected Response:**
```json
{
  "reply": "I hear you, and I appreciate you reaching out 💙 Things can feel really heavy when stress piles up. Please take a gentle, deep breath..."
}
```

---

## 4. Live vs. Demo Mode

- **LIVE (`mode: "live"`)**: The real Qwen3-4B neural network runs inference on the CPU and generates the response.
- **DEMO (`mode: "demo"`)**: Transparent fallback engine. Automatically activates if the model file is missing, llama-server fails to start, or memory allocation fails. Detailed diagnostics are logged to console.

---

## 5. Automated Test Suite

Run the full 6-stage test suite:
```powershell
.\.venv\Scripts\python.exe -X utf8 test_endpoints.py
```

This verifies:
1. `GET /health` (`mode: live`)
2. English emotional generation
3. Tanglish generation
4. Tamil script Unicode generation
5. Deterministic crisis safety guardrail (Tele-MANAS 14416 / 112)
6. Multi-turn conversation context memory
7. Response latency & RAM delta

---

## 6. Performance & Memory Considerations

### Hardware Profile:
- **Processor**: Intel Core i5-12450H (8 Cores, 12 Logical Processors)
- **RAM**: 16 GB DDR4/DDR5
- **Accelerator**: None (Intel UHD Graphics, CPU inference only)

### Observed Metrics:
- **llama-server Startup**: ~7.8 seconds
- **Verification Inference Latency**: ~0.8 seconds
- **Inference Speed**: ~11.1 tokens/second (direct), ~2.7–3.5 tokens/second (full HTTP JSON pipeline)
- **RAM at rest**: ~10.5 GB used by Windows & apps
- **RAM under Model Load**: ~14.7 GB used (+4.2 GB for GGUF model weights, KV cache, and inference buffers)
- **Available Headroom**: ~1.0 GB physical RAM

### Troubleshooting:
- **Port Conflicts**: Ensure port `8000` (FastAPI) and port `8081` (llama-server) are free. Use `powershell -Command "Stop-Process -Name llama-server -Force"` if a previous process was not stopped cleanly.
- **Unicode Support**: On Windows PowerShell, pass `-X utf8` or set `$env:PYTHONIOENCODING='utf-8'` when viewing Tamil Unicode scripts and emoji in the terminal.
- **Fallback Transparency**: If `llama-server.exe` fails to respond within timeout or exits, FastAPI will log the exact reason (`[QWEN] LIVE INFERENCE FAILED: <reason>`) and transparently serve deterministic demo replies with `mode: "demo"`.

