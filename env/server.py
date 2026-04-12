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

import gradio as gr

# --- Gradio Web UI ---
with gr.Blocks(title="Gatekeeper Demo", theme=gr.themes.Default(primary_hue="blue")) as demo:
    gr.Markdown("# 🛡️ Gatekeeper - OpenEnv Cybersecurity Demo")
    gr.Markdown("Interactive WAF Simulator to train RL agents against DoS/DDoS attacks.")
    
    with gr.Row():
        with gr.Column(scale=1):
            action_type = gr.Dropdown(
                choices=["noop", "block_ip", "rate_limit_ip", "rate_limit_path", "enable_challenge", "add_waf_rule", "whitelist_ip", "clear_actions"], 
                label="Action Type", 
                value="noop"
            )
            ip_param = gr.Textbox(label="Target IP (Optional)", placeholder="e.g. 10.0.0.5")
            step_btn = gr.Button("Step Environment", variant="primary")
            reset_btn = gr.Button("Reset Environment")
        
        with gr.Column(scale=2):
            result_json = gr.JSON(label="Step Output (Observation & Reward)")
            state_json = gr.JSON(label="Internal State Dump")

    async def do_step(act_type, ip):
        params = {}
        if ip: params["ip"] = ip
        if act_type in ["block_ip", "rate_limit_ip", "enable_challenge"]:
           params["duration"] = 60
        act = ActionModel(action_type=act_type, parameters=params)
        res = await env.step(act)
        return res, env.state()

    async def do_reset():
        res = await env.reset()
        return res, env.state()

    step_btn.click(do_step, inputs=[action_type, ip_param], outputs=[result_json, state_json])
    reset_btn.click(do_reset, inputs=[], outputs=[result_json, state_json])

app = gr.mount_gradio_app(app, demo, path="/")