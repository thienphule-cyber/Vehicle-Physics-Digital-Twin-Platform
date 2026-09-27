"""
Application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import vehicles, simulation, analysis, validation, comparison

app = FastAPI(title="Vehicle Physics Digital Twin Platform - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(simulation.router)
app.include_router(analysis.router)
app.include_router(validation.router)
app.include_router(comparison.router)


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok"}