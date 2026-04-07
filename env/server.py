import os
from fastapi import FastAPI, HTTPException
from typing import Dict, Any

from .gatekeeper_env import GatekeeperEnv
from .models import ActionModel

# --- FastAPI Initialization ---
app = FastAPI(title="Gatekeeper OpenEnv Server")
env = GatekeeperEnv()

@app.post("/reset")
async def reset():
    """Reset the environment to start a new episode."""
    try:
        return await env.reset()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step(action: ActionModel):
    """Apply an action and receive state/reward feedback."""
    try:
        return await env.step(action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
async def get_state():
    """Access the ground-truth internal environment state."""
    return env.state()

@app.get("/health")
async def health():
    """Environment health and readiness check."""
    return {"status": "healthy", "env": "gatekeeper"}

@app.get("/")
async def root():
    return {"message": "Gatekeeper OpenEnv Server is running"}