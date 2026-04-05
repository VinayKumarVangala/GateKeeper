import asyncio
import os
# Future Import: OpenAI client
# from openai import OpenAI

from env.gatekeeper_env import GatekeeperEnv
from env.models import ActionModel

async def main():
    """
    Main entrypoint for baseline agent inference.
    Executes a simple interaction loop with the Gatekeeper environment.
    """
    print("[START] Initializing Gatekeeper Environment")
    env = GatekeeperEnv()
    
    # Reset Environment
    obs = await env.reset()
    
    # 1. Initialize LLM / Model Client (OpenAI, Anthropic, HuggingFace)
    # client = OpenAI(api_key=os.getenv("HF_TOKEN"))
    
    # Loop over steps (5 minutes = 300 steps)
    for step_count in range(300):
        # 2. Present observation to LLM agent
        # response = client.chat.completions.create(...)
        # action_data = response.choices[0].message.content
        
        # 3. Take an action in OpenEnv
        # Placeholder Action: Do Nothing
        action = ActionModel(action_type="noop", parameters={})
        next_obs, reward, done, info = await env.step(action)
        
        # 4. Mandatory Log format for evaluation
        print(f"[STEP] step={step_count} reward={reward} done={done}")
        
        if done:
            break
            
    # Finalize
    print("[END] Final Grade Calculation / Environment Termination")

if __name__ == "__main__":
    asyncio.run(main())
