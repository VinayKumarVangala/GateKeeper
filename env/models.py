from pydantic import BaseModel
from typing import Dict, Any, List

class ObservationModel(BaseModel):
    """
    Structured traffic insights for the agent at each step.
    """
    traffic_summary: Dict[str, Any]
    anomaly_scores: Dict[str, float]
    active_rules: List[str]
    timestamp: float

class ActionModel(BaseModel):
    """
    Represent an action taken by the agent.
    """
    action_type: str
    parameters: Dict[str, Any]

class StateModel(BaseModel):
    """
    Internal environment state, including full history.
    """
    raw_logs: List[Dict[str, Any]]
    active_mitigations: Dict[str, Any]
    current_step: int
    attack_status: bool
