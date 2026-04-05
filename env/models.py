from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
import json

class ObservationModel(BaseModel):
    """
    Represents the structured traffic insights visible to the agent at each simulation step.
    This model acts as the input 'observation' for the RL agent.
    """
    traffic_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Requests per IP or entity. Example: {'1.2.3.4': 100}"
    )
    endpoint_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Requests per endpoint/path. Example: {'/login': 50}"
    )
    error_rates: Dict[str, float] = Field(
        default_factory=dict,
        description="Ratio of failed requests (4xx/5xx) per IP. Range: 0.0 to 1.0"
    )
    anomaly_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Computed suspicion level per IP or path. Range: 0.0 (safe) to 1.0 (malicious)"
    )
    active_rules: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of mitigation rules currently enforced by the WAF."
    )
    timestamp: int = Field(
        default=0,
        description="Current simulation time step (seconds elapsed since start)."
    )

    @validator("anomaly_scores")
    def validate_anomaly_scores_range(cls, v):
        for key, score in v.items():
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"Anomaly score for {key} must be between 0.0 and 1.0. Got: {score}")
        return v

    @validator("timestamp")
    def validate_timestamp_non_negative(cls, v):
        if v < 0:
            raise ValueError("Timestamp cannot be negative.")
        return v

    class Config:
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "traffic_summary": {"10.0.0.5": 120, "192.168.1.1": 15},
                "endpoint_summary": {"/login": 40, "/api/v1/resource": 85},
                "error_rates": {"10.0.0.5": 0.45},
                "anomaly_scores": {"10.0.0.5": 0.92, "/login": 0.3},
                "active_rules": [{"type": "block_ip", "target": "10.0.0.5"}],
                "timestamp": 45
            }
        }


class ActionModel(BaseModel):
    """
    Represents an action chosen by the agent to mitigate perceived threats.
    """
    action_type: str = Field(
        ...,
        description="Type of mitigation action. Allowed: block_ip, rate_limit_ip, rate_limit_path, enable_challenge, add_waf_rule, whitelist_ip, clear_actions"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible payload containing target IP, path, limit, or duration."
    )

    class Config:
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "action_type": "rate_limit_ip",
                "parameters": {"ip": "1.2.3.4", "limit": 10, "duration": 60}
            }
        }


class StateModel(BaseModel):
    """
    Internal environment state representing the 'ground truth' of the simulation.
    Contains raw data, full history, and hidden indicators not directly visible to the agent.
    """
    raw_logs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Buffer of raw traffic logs generated in the current step."
    )
    aggregated_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Cached global metrics and historical counters."
    )
    active_mitigations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Internal master list of active WAF rules and their expiry timers."
    )
    attack_flags: Dict[str, bool] = Field(
        default_factory=dict,
        description="Current ground-truth status of active attacks (e.g., {'ddos': True})."
    )
    current_step: int = Field(
        default=0,
        description="Monotonic simulation step counter."
    )

    class Config:
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "raw_logs": [{"ip": "1.2.3.4", "path": "/login", "status": 200}],
                "aggregated_stats": {"total_requests": 1500, "unique_ips": 45},
                "active_mitigations": [{"type": "block_ip", "ip": "1.2.3.4", "expires_at": 300}],
                "attack_flags": {"ddos": True, "bruteforce": False},
                "current_step": 12
            }
        }

# --- Example Usage (Documentation) ---
# 
# observation = ObservationModel(
#     traffic_summary={"1.1.1.1": 50},
#     endpoint_summary={"/api": 10},
#     timestamp=5
# )
# 
# action = ActionModel(
#     action_type="block_ip",
#     parameters={"ip": "1.1.1.1"}
# )
# 
# state = StateModel(
#     attack_flags={"ddos": True},
#     current_step=5
# )
