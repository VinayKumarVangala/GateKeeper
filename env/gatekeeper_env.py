import asyncio
import random
from typing import Dict, Any, Tuple, List, Optional
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
        return self._build_observation([])

    def _cleanup_expired_rules(self):
        """
        Removes mitigation rules whose duration has elapsed.
        Called at the start of every step.
        """
        self._state.active_mitigations = [
            rule for rule in self._state.active_mitigations 
            if self._state.current_step < rule.get("expires_at", float('inf'))
        ]

    def _apply_action(self, action: ActionModel, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Action Execution Engine:
        1. Clean expired rules.
        2. Update mitigations with new action.
        3. Apply persistent + new mitigations to traffic logs.
        """
        # 1. Cleanup before processing
        self._cleanup_expired_rules()

        # 2. Add New Action to Active Mitigations (if applicable)
        if action.action_type != "noop" and action.action_type != "clear_actions":
            params = action.parameters
            duration = params.get("duration", 60) # Default 60s
            
            new_rule = {
                "type": action.action_type,
                "target": params.get("ip") or params.get("path") or params.get("target"),
                "expires_at": self._state.current_step + duration,
                "params": params
            }
            self._state.active_mitigations.append(new_rule)
        elif action.action_type == "clear_actions":
            self._state.active_mitigations = []

        # 3. Apply ALL current active mitigations to the logs in a specific order
        # Correct Order: block_ip -> rate_limit_ip -> enable_challenge -> waf_rule
        rule_priority = {
            "block_ip": 1,
            "rate_limit_ip": 2,
            "enable_challenge": 3,
            "waf_rule": 4
        }
        
        # Sort rules based on priority
        sorted_rules = sorted(
            self._state.active_mitigations, 
            key=lambda x: rule_priority.get(x["type"], 99)
        )

        filtered_logs = logs
        for rule in sorted_rules:
            rule_type = rule["type"]
            target = rule["target"]
            params = rule.get("params", {})

            if rule_type == "block_ip":
                filtered_logs = [log for log in filtered_logs if log["ip"] != target]
            
            elif rule_type == "rate_limit_ip":
                limit = params.get("limit", 10)
                ip_counts: Dict[str, int] = {}
                new_logs = []
                for log in filtered_logs:
                    if log["ip"] == target:
                        ip_counts[target] = ip_counts.get(target, 0) + 1
                        if ip_counts[target] <= limit:
                            new_logs.append(log)
                    else:
                        new_logs.append(log)
                filtered_logs = new_logs

            elif rule_type == "waf_rule":
                field = params.get("field", "path")
                pattern = params.get("pattern", "")
                waf_action = params.get("action", "block")
                
                if waf_action == "block":
                    filtered_logs = [log for log in filtered_logs if log.get(field) != pattern]
                elif waf_action == "allow":
                    # For simplicity, 'allow' keeps logs that match, 
                    # but doesn't necessarily block others unless there's a default-deny
                    pass 

            elif rule_type == "enable_challenge":
                # Reduce matching traffic by ~50% (CAPTCHA simulation)
                filtered_logs = [
                    log for log in filtered_logs 
                    if not (log["ip"] == target and random.random() < 0.5)
                ]

        return filtered_logs

    def _build_observation(self, logs: List[Dict[str, Any]]) -> ObservationModel:
        """
        Aggregates raw traffic logs into a structured ObservationModel.
        """
        traffic_summary: Dict[str, int] = {}
        endpoint_summary: Dict[str, int] = {}
        error_counts: Dict[str, int] = {}
        
        for log in logs:
            ip = log["ip"]
            path = log["path"]
            status = log["status"]
            traffic_summary[ip] = traffic_summary.get(ip, 0) + 1
            endpoint_summary[path] = endpoint_summary.get(path, 0) + 1
            if status >= 400:
                error_counts[ip] = error_counts.get(ip, 0) + 1

        error_rates: Dict[str, float] = {}
        anomaly_scores: Dict[str, float] = {}
        VOLUME_THRESHOLD = 50.0

        for ip, count in traffic_summary.items():
            ip_errors = error_counts.get(ip, 0)
            rate = ip_errors / count
            error_rates[ip] = rate
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
        # 1. Fetch Raw Traffic Logs (Future Phase Integration)
        # For now, placeholder or generator call
        raw_logs = [] # self.traffic_gen.generate_...()
        
        # 2. Apply Mitigation Action
        filtered_logs = self._apply_action(action, raw_logs)
        
        # 3. Calculate Reward (Future Phase)
        reward = self.reward_engine.compute_reward(self._state, action)
        
        # 4. Advance State
        self._state.current_step += 1
        if self._state.current_step >= 300:
            self.is_done = True
            
        # 5. Return Observation
        return self._build_observation(filtered_logs), reward, self.is_done, {}

    def state(self) -> StateModel:
        """
        Accessor for the full internal environment state.
        """
        return self._state

# --- Example Logic (Documentation) ---
# logs = [ {"ip": "1.1.1.1", "path": "/login", "status": 401}, ... ]
# action = ActionModel(action_type="block_ip", parameters={"ip": "1.1.1.1"})
# Result: filtered_logs = []
