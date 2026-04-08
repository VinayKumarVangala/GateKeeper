import os
import asyncio
import json
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

from env.gatekeeper_env import GatekeeperEnv
from env.models import ActionModel

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
# Use lightweight free model
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
MAX_STEPS = 300
MAX_TOTAL_REWARD = 500.0

# Synchronous client for deterministic OpenEnv benchmark compliance
client = OpenAI(base_url=API_BASE_URL, api_key=os.getenv("HF_TOKEN"))

# --- Logging Functions (STRICT FORMAT) ---
def log_start(task: str, env_name: str, model: str):
    print(f"[START] task={task} env={env_name} model={model}")

def log_step(step: int, action: str, reward: float, done: bool, error: str = "null"):
    done_str = "true" if done else "false"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error or 'null'}")

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    success_str = "true" if success else "false"
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END] success={success_str} steps={steps} score={score:.2f} rewards={rewards_str}")

# --- Helper for fallback action when LLM fails ---
def _fallback_action(observation: Any) -> str:
    """Return a JSON string with a safe fallback action.

    Preference order:
    1. If anomaly_scores are present, block the IP with the highest score.
    2. Otherwise, apply a generic rate_limit_ip.
    """
    # Extract dict safely for different Pydantic versions
    obs_dict = observation.model_dump() if hasattr(observation, "model_dump") else observation.dict()
    anomaly_scores = obs_dict.get("anomaly_scores", {})
    if anomaly_scores:
        # Pick IP with highest anomaly score
        ip = max(anomaly_scores.items(), key=lambda kv: kv[1])[0]
        fallback = {"action_type": "block_ip", "parameters": {"ip": ip, "duration": 60}}
    else:
        # Generic safe rate limit (use a placeholder IP)
        fallback = {"action_type": "rate_limit_ip", "parameters": {"ip": "0.0.0.0", "limit": 10, "duration": 60}}
    return json.dumps(fallback)

# --- Agent Logic ---
def get_model_action(observation: Any, history: List[str]) -> str:
    """Construct a prompt and query the LLM for a mitigation action.
    If the API call fails, a deterministic fallback action is returned.
    """
    history_context = "\n".join(list(history)[-5:])

    # Extract dict safely for different Pydantic versions
    obs_dict = observation.model_dump() if hasattr(observation, "model_dump") else observation.dict()

    prompt = f"""
    You are a Gatekeeper WAF. Analyze the traffic and take a mitigation action.

    Current Observation:
    {json.dumps(obs_dict, indent=2)}

    Previous History:
    {history_context}

    Available Actions:
    - block_ip(ip=\"x.x.x.x\", duration=60)
    - rate_limit_ip(ip=\"x.x.x.x\", limit=10, duration=60)
    - enable_challenge(target=\"x.x.x.x\", duration=60)
    - noop()

    Output ONLY JSON in the format: {{"action_type": "...", "parameters": {{...}}}}
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Return a safe deterministic fallback action
        return _fallback_action(observation)

def parse_action(action_str: str) -> ActionModel:
    """Convert model raw output into an ActionModel."""
    try:
        data = json.loads(action_str)
        return ActionModel(
            action_type=data.get("action_type", "noop"),
            parameters=data.get("parameters", {}),
        )
    except Exception:
        return ActionModel(action_type="noop", parameters={})

# --- Main loop ---
async def main():
    env = GatekeeperEnv()
    history: List[str] = []
    rewards: List[float] = []
    task_name = "gatekeeper"
    env_name = "cybersec"

    log_start(task_name, env_name, MODEL_NAME)

    try:
        # Start Episode
        result = await env.reset()
        obs = result["observation"]

        for step in range(1, MAX_STEPS + 1):
            # 1. Generate Action
            raw_action = get_model_action(obs, history)
            action = parse_action(raw_action)

            # 2. Execute Step
            try:
                res = await env.step(action)
                obs = res["observation"]
                reward = res["reward"]
                done = res["done"]
                error = "null"
            except Exception as e:
                reward = 0.0
                done = True
                error = str(e)

            # 3. Logging & Tracking
            log_step(step, action.action_type, reward, done, error)
            rewards.append(reward)
            history.append(f"Step {step}: Action={action.action_type}, Reward={reward:.2f}")

            if done:
                break

        # Calculate Final Score for normalized report (strictly between 0 and 1)
        total_rewards = sum(rewards)
        score = max(0.0, min(total_rewards / MAX_TOTAL_REWARD, 0.99))
        log_end(success=True, steps=len(rewards), score=score, rewards=rewards)

    except Exception as e:
        log_end(success=False, steps=len(rewards), score=0.0, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
