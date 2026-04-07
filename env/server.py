import os
from fastapi import FastAPI, HTTPException
from typing import Dict, Any
from env.gatekeeper_env import GatekeeperEnv
from env.models import ActionModel

# Create FastAPI app instance
app = FastAPI(title="Gatekeeper OpenEnv Server")

# Global environment instance (Simplified for demo)
env = GatekeeperEnv()

@app.post("/reset")
async def reset():
    """Reset the Gatekeeper environment."""
    try:
        return await env.reset()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step(action: ActionModel):
    """Execute a mitigation step in the environment."""
    try:
        return await env.step(action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
async def get_state():
    """Retrieve the full internal state (for debugging/grading)."""
    return env.state()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "env": "gatekeeper"}

@app.get("/")
async def root():
    return {
        "message": "Gatekeeper OpenEnv is running 🚀",
        "endpoints": {
            "reset": "/reset (POST)",
            "step": "/step (POST)",
            "state": "/state (GET)",
            "health": "/health (GET)"
        }
    }