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
with gr.Blocks(title="Gatekeeper Demo", theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate")) as demo:
    gr.Markdown(
        """
        <div style="text-align: center;">
            <h1>🛡️ Gatekeeper - OpenEnv Cybersecurity Demo</h1>
            <p>Interactive Web Application Firewall (WAF) Simulator to train and evaluate RL agents against DoS/DDoS computational attacks.</p>
        </div>
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                gr.Markdown("### 📡 Security Control Panel")
                action_type = gr.Dropdown(
                    choices=["noop", "block_ip", "rate_limit_ip", "rate_limit_path", "enable_challenge", "add_waf_rule", "whitelist_ip", "clear_actions"], 
                    label="Action Type", 
                    value="noop",
                    info="Select the mitigation action to apply in the simulation."
                )
                ip_param = gr.Textbox(
                    label="Target Entity (Optional)", 
                    placeholder="e.g. 10.0.0.5 or /api/login",
                    info="Specify the IP address or endpoint path to apply the action onto."
                )
                
            with gr.Row():
                step_btn = gr.Button("▶ Step Environment", variant="primary", scale=2)
                reset_btn = gr.Button("🔄 Reset Episode", variant="secondary", scale=1)
                
            with gr.Accordion("ℹ️ How to Use", open=False):
                gr.Markdown(
                    """
                    1. **Reset Episode:** Start a new network traffic simulation.
                    2. **Select Action:** Choose a WAF mitigation strategy from the dropdown. 
                        - `noop`: Monitor traffic without intervention.
                        - `block_ip`: Completely blocks an IP address.
                        - `rate_limit_ip`: Throttles requests from a specific IP.
                        - `rate_limit_path`: Throttles all requests to a specific path.
                        - `enable_challenge`: Forces a CAPTCHA challenge for a source.
                        - `add_waf_rule`: Dynamically deploy a firewall rule.
                        - `whitelist_ip`: Explicitly trust an IP to bypass limits.
                        - `clear_actions`: Flush active mitigation rules to factory state.
                    3. **Target Entity:** Enter the suspicious IP or endpoint, if your action requires a target.
                    4. **Step Environment:** Apply the action and advance the simulation by one step. Observe the changes in network traffic and your defensive reward.
                    """
                )
                
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("📊 Observation & Reward"):
                    result_json = gr.JSON(label="Last Step Output")
                with gr.TabItem("⚙️ Internal State"):
                    state_json = gr.JSON(label="Full Environment Dump")

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