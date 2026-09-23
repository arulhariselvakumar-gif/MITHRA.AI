"""
FastAPI application entrypoint for the Mithra AI Microservice.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import GenerateRequest, GenerateResponse, HealthResponse
from app.model import load_model, shutdown_model, generate_reply, get_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: load model at startup, clean up on shutdown."""
    load_model()
    yield
    shutdown_model()


app = FastAPI(
    title="Mithra AI Microservice",
    description="Dedicated AI companion microservice powering Mithra with Qwen3-4B",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local development and Express communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint returning system status and active model.
    Response: {"status": "ok", "model": "Qwen3-4B", "mode": "live"|"demo"}
    """
    info = get_status()
    return HealthResponse(
        status=info["status"],
        model=info["model"],
        mode=info["mode"]
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    Inference endpoint:
    Accepts user message, history, and preferred language, returning Mithra's reply.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'message' cannot be empty."
        )

    try:
        reply = generate_reply(
            message=req.message.strip(),
            history=req.history,
            language=req.language or "English"
        )
        return GenerateResponse(reply=reply)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(exc)}"
        )
