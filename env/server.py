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

import json
import gradio as gr

def format_obs(data):
    if not data: return "No data yet."
    obs = data.get("observation", {})
    reward = data.get("reward", 0.0)
    done = data.get("done", False)
    
    md = f"**Episode Status:** {'Finished' if done else 'Ongoing'} | **Step Reward:** `{reward:.2f}`\\n\\n"
    
    md += "### 🌐 Traffic Summary (IPs)\\n"
    if obs.get("traffic_summary"):
        for ip, count in obs["traffic_summary"].items(): md += f"- **{ip}**: {count} requests\\n"
    else: md += "- No traffic\\n"

    md += "\\n### 🛣️ Endpoint Summary\\n"
    if obs.get("endpoint_summary"):
        for path, count in obs["endpoint_summary"].items(): md += f"- **{path}**: {count} requests\\n"
    else: md += "- No API traffic\\n"
    
    md += "\\n### 🚨 Anomaly Scores\\n"
    if obs.get("anomaly_scores"):
        for ip, score in obs["anomaly_scores"].items(): md += f"- **{ip}**: {score:.2f} \\n"
    else: md += "- All clear\\n"

    md += "\\n### 🛡️ Active Rules\\n"
    rules = obs.get("active_rules", [])
    if rules:
        for rule in rules: md += f"- `{rule}`\\n"
    else: md += "- No rules active\\n"

    return md

def format_internal_state(state):
    if not state: return "No internal state yet."
    md = "### ⚙️ Internal Environment Variables\\n"
    try:
        # Use simple dict-to-string for objects that may not be JSON serializable
        if hasattr(state, '__dict__'): state = state.__dict__
        for key, value in state.items():
            if hasattr(value, '__dict__'): value = value.__dict__
            md += f"**{key}:**\\n```python\\n{value}\\n```\\n\\n"
        return md
    except Exception as e:
        return f"```python\\n{state}\\n```"

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
    
    # Store internal data 
    current_obs_data = gr.State({})
    current_state_data = gr.State({})

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
                    obs_view_mode = gr.Radio(["FORMATTED", "RAW (JSON)"], label="View Mode", value="FORMATTED")
                    with gr.Group() as obs_formatted_group:
                        obs_md = gr.Markdown("No data yet.")
                    with gr.Group(visible=False) as obs_raw_group:
                        result_json = gr.JSON(label="Last Step Output")
                        
                with gr.TabItem("⚙️ Internal State"):
                    state_view_mode = gr.Radio(["FORMATTED", "RAW (JSON)"], label="View Mode", value="FORMATTED")
                    with gr.Group() as state_formatted_group:
                        state_md = gr.Markdown("No state yet.")
                    with gr.Group(visible=False) as state_raw_group:
                        state_json = gr.JSON(label="Full Environment Dump")

    async def core_step(act_type, ip):
        params = {}
        if ip: params["ip"] = ip
        if act_type in ["block_ip", "rate_limit_ip", "enable_challenge"]:
           params["duration"] = 60
        act = ActionModel(action_type=act_type, parameters=params)
        res = await env.step(act)
        st = env.state()
        return res, st
        
    async def core_reset():
        res = await env.reset()
        return res, env.state()

    def update_obs_ui(data, mode):
        if mode == "FORMATTED":
            return format_obs(data), gr.update(visible=True), gr.update(visible=False), data
        else:
            return "", gr.update(visible=False), gr.update(visible=True), data

    def update_state_ui(data, mode):
        if mode == "FORMATTED":
            return format_internal_state(data), gr.update(visible=True), gr.update(visible=False), data
        else:
            return "", gr.update(visible=False), gr.update(visible=True), data

    async def process_step(act_type, ip, omode, smode):
        res, st = await core_step(act_type, ip)
        return res, st, *update_obs_ui(res, omode)[:3], *update_state_ui(st, smode)[:3], res, st
        
    async def process_reset(omode, smode):
        res, st = await core_reset()
        return res, st, *update_obs_ui(res, omode)[:3], *update_state_ui(st, smode)[:3], res, st

    step_btn.click(
        process_step,
        inputs=[action_type, ip_param, obs_view_mode, state_view_mode],
        outputs=[current_obs_data, current_state_data, obs_md, obs_formatted_group, obs_raw_group, state_md, state_formatted_group, state_raw_group, result_json, state_json]
    )

    reset_btn.click(
        process_reset,
        inputs=[obs_view_mode, state_view_mode],
        outputs=[current_obs_data, current_state_data, obs_md, obs_formatted_group, obs_raw_group, state_md, state_formatted_group, state_raw_group, result_json, state_json]
    )

    obs_view_mode.change(
        update_obs_ui,
        inputs=[current_obs_data, obs_view_mode],
        outputs=[obs_md, obs_formatted_group, obs_raw_group, result_json]
    )

    state_view_mode.change(
        update_state_ui,
        inputs=[current_state_data, state_view_mode],
        outputs=[state_md, state_formatted_group, state_raw_group, state_json]
    )

app = gr.mount_gradio_app(app, demo, path="/")