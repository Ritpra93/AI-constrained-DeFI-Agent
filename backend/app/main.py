"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="DeFi Agent Backend",
    description="Orchestration service for AI Risk-Constrained DeFi Agent",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
