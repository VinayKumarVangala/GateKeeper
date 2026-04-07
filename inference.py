import os
import asyncio
import json
from typing import List, Dict, Any
from openai import OpenAI

from env.gatekeeper_env import GatekeeperEnv
from env.models import ActionModel

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or "placeholder"
MAX_STEPS = 300
MAX_TOTAL_REWARD = 500.0  # Estimated max reward for normalization

from openai import AsyncOpenAI
client = AsyncOpenAI(base_url=API_BASE_URL, api_key=API_KEY, timeout=30.0)

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

# --- Agent Logic ---
async def get_model_action(observation: Any, history: List[str]) -> str:
    """
    Constructs a prompt and queries the AI model for a defense action.
    """
    # Cast to List to resolve potential linter slicing issues
    history_context = "\n".join(list(history)[-5:]) 
    
    # Extract dict safely for different Pydantic versions
    obs_dict = observation.model_dump() if hasattr(observation, 'model_dump') else observation.dict()
    
    prompt = f"""
    You are a Gatekeeper WAF. Analyze the traffic and take a mitigation action.
    
    Current Observation:
    {json.dumps(obs_dict, indent=2)}
    
    Previous History:
    {history_context}
    
    Available Actions:
    - block_ip(ip="x.x.x.x", duration=60)
    - rate_limit_ip(ip="x.x.x.x", limit=10, duration=60)
    - enable_challenge(target="x.x.x.x", duration=60)
    - noop()
    
    Output ONLY JSON in the format: {{"action_type": "...", "parameters": {{...}}}}
    """
    
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.0 # Deterministic
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return '{"action_type": "noop", "parameters": {}}'

def parse_action(action_str: str) -> ActionModel:
    """
    Converts model raw output into an ActionModel.
    """
    try:
        data = json.loads(action_str)
        return ActionModel(
            action_type=data.get("action_type", "noop"),
            parameters=data.get("parameters", {})
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
            raw_action = await get_model_action(obs, history)
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
        
        # Calculate Final Score
        total_rewards = sum(rewards)
        score = min(max(total_rewards / MAX_TOTAL_REWARD, 0.0), 1.0)
        log_end(success=True, steps=len(rewards), score=score, rewards=rewards)

    except Exception as e:
        # Emergency Shutdown Logging
        log_end(success=False, steps=len(rewards), score=0.0, rewards=rewards)
        # print(f"Fatal Error: {e}") # Standard error only

if __name__ == "__main__":
    asyncio.run(main())
