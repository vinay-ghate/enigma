"""
FastAPI Server Entrypoint for Enigma.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Incident root-cause investigation engine using Google ADK agents and a NetworkX causal graph.",
    version="0.2.0",
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "engine": "networkx-adk",
        "default_mode": settings.DEFAULT_MODE,
        "sandbox_repo": settings.SANDBOX_REPO,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
