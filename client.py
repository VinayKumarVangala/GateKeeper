import httpx
import os
from typing import Dict, Any, Optional
from env.models import ActionModel, ObservationModel

class GatekeeperClient:
    """
    Standard client for interacting with the Gatekeeper OpenEnv,
    either locally or via a deployed Hugging Face Space.
    """

    def __init__(self, base_url: str = "http://localhost:7860", token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token or os.getenv("HF_TOKEN") or ""
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def reset(self) -> Dict[str, Any]:
        """Resets the environment and returns the initial observation."""
        with httpx.Client(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
            response = client.post("/reset")
            response.raise_for_status()
            return response.json()

    def step(self, action_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Pushes an action to the environment."""
        with httpx.Client(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
            response = client.post("/step", json=action_dict)
            response.raise_for_status()
            return response.json()

    def state(self) -> Dict[str, Any]:
        """Retrieves the full internal state."""
        with httpx.Client(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
            response = client.get("/state")
            response.raise_for_status()
            return response.json()

# For local evaluation or quick CLI tests
if __name__ == "__main__":
    client = GatekeeperClient()
    try:
        obs = client.reset()
        print(f"Reset Success: {obs['observation']['timestamp']}")
    except Exception as e:
        print(f"Connection Failed: {e}")
