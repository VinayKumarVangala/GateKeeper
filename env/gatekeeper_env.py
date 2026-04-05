import asyncio
from typing import Dict, Any, Tuple, List
from .models import ObservationModel, ActionModel, StateModel
from .traffic_generator import TrafficGenerator
from .reward_engine import RewardEngine

class GatekeeperEnv:
    """
    OpenEnv-compatible Reinforcement Learning environment for Cybersecurity defense.
    Simulates Realistic Network Traffic and WAF-like Mitigation Strategies.
    """

    def __init__(self):
        self.traffic_gen = TrafficGenerator()
        self.reward_engine = RewardEngine()
        self._state: StateModel = StateModel(
            raw_logs=[],
            aggregated_stats={},
            active_mitigations=[],
            attack_flags={},
            current_step=0
        )
        self.is_done = False

    async def reset(self) -> ObservationModel:
        """
        Initializes the environment state and returns the first observation.
        """
        self._state = StateModel(
            raw_logs=[],
            aggregated_stats={},
            active_mitigations=[],
            attack_flags={},
            current_step=0
        )
        self.is_done = False
        
        # Build first observation (empty)
        return self._build_observation([])

    def _build_observation(self, logs: List[Dict[str, Any]]) -> ObservationModel:
        """
        Aggregates raw traffic logs into a structured ObservationModel.
        
        Logic:
        1. Count requests per IP and Path.
        2. Calculate error rates per IP (status >= 400).
        3. Compute anomaly heuristics based on volume and errors.
        """
        traffic_summary: Dict[str, int] = {}
        endpoint_summary: Dict[str, int] = {}
        error_counts: Dict[str, int] = {}
        
        # O(n) pass over logs for aggregation
        for log in logs:
            ip = log["ip"]
            path = log["path"]
            status = log["status"]
            
            # Count per IP
            traffic_summary[ip] = traffic_summary.get(ip, 0) + 1
            # Count per Path
            endpoint_summary[path] = endpoint_summary.get(path, 0) + 1
            # Count errors
            if status >= 400:
                error_counts[ip] = error_counts.get(ip, 0) + 1

        # Calculate Error Rates and Anomaly Scores
        error_rates: Dict[str, float] = {}
        anomaly_scores: Dict[str, float] = {}
        
        # Tunable Threshold for Volume-based suspicion
        VOLUME_THRESHOLD = 50.0

        for ip, count in traffic_summary.items():
            # Error Rate
            ip_errors = error_counts.get(ip, 0)
            rate = ip_errors / count
            error_rates[ip] = rate
            
            # Anomaly Score Heuristic: Combine Volume and Error Rate
            # Normalize volume (min 0, max 1.0) and add error bias
            volume_score = count / VOLUME_THRESHOLD
            score = min(1.0, volume_score + rate)
            anomaly_scores[ip] = score

        return ObservationModel(
            traffic_summary=traffic_summary,
            endpoint_summary=endpoint_summary,
            error_rates=error_rates,
            anomaly_scores=anomaly_scores,
            active_rules=self._state.active_mitigations,
            timestamp=self._state.current_step
        )

    async def step(self, action: ActionModel) -> Tuple[ObservationModel, float, bool, Dict[str, Any]]:
        """
        Executes an action, advances the simulation, and returns the next step data.
        """
        # Note: Full execution loop will be implemented in later phases
        # For now, we increment step and return state-matched observation
        
        reward = self.reward_engine.compute_reward(self._state, action)
        self._state.current_step += 1
        
        if self._state.current_step >= 300:
            self.is_done = True
            
        # Placeholders for generated logs in this step
        logs = [] # Will be populated by traffic_gen.step() in Phase 8
            
        return self._build_observation(logs), reward, self.is_done, {}

    def state(self) -> StateModel:
        """
        Accessor for the full internal environment state.
        """
        return self._state

# --- Example Logic (Documentation) ---
# Input logs: [{"ip": "1.1.1.1", "path": "/login", "status": 401}]
# traffic_summary = {"1.1.1.1": 1}
# error_rates = {"1.1.1.1": 1.0}
# anomaly_scores = {"1.1.1.1": 1.0} (due to 100% error rate + base volume)
