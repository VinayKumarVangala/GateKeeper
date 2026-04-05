import asyncio
import random
from typing import Dict, Any, Tuple, List, Optional
from .models import ObservationModel, ActionModel, StateModel
from .traffic_generator import TrafficGenerator
from .reward_engine import RewardEngine

class GatekeeperEnv:
    """
    OpenEnv-compatible Reinforcement Learning environment for Cybersecurity defense.
    Orchestrates: Traffic -> Action -> State Update -> Reward -> Observation.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.traffic_gen = TrafficGenerator(seed=seed)
        self.reward_engine = RewardEngine()
        self._state: Optional[StateModel] = None
        self.is_done = False

    async def reset(self) -> Dict[str, Any]:
        """
        Initializes the environment state and returns the first observation.
        """
        # Re-initialize core components
        self.traffic_gen = TrafficGenerator(seed=self.seed)
        self.reward_engine = RewardEngine()
        
        self._state = StateModel(
            raw_logs=[],
            aggregated_stats={},
            active_mitigations=[],
            attack_flags={"bruteforce": False, "ddos": False, "multivector": False},
            current_step=0
        )
        self.is_done = False
        
        # Generate initial "normal" traffic logs
        initial_logs = self.traffic_gen.step(mode="normal")
        
        # Build first observation
        observation = self._build_observation(initial_logs)
        
        return {
            "observation": observation,
            "reward": 0.0,
            "done": False,
            "info": {"step": 0, "mode": "normal"}
        }

    def _get_current_mode(self) -> str:
        """
        Heuristic to determine the current traffic mode based on time progression.
        Allows for challenging, multi-phase episodes.
        """
        step = self._state.current_step
        if step < 100:
            return "normal"
        elif step < 200:
            return "bruteforce"
        elif step < 250:
            return "ddos"
        return "multivector"

    async def step(self, action: ActionModel) -> Dict[str, Any]:
        """
        Advances the simulation by one step.
        Flow: Traffic -> Mitigation -> Reward -> Next State.
        """
        if self._state is None:
            raise RuntimeError("Environment must be reset() before calling step().")

        # 1. Increment Step
        self._state.current_step += 1
        
        # 2. Generate Traffic for current mode
        mode = self._get_current_mode()
        self._state.attack_flags = {
            "bruteforce": mode == "bruteforce",
            "ddos": mode == "ddos",
            "multivector": mode == "multivector"
        }
        
        raw_logs = self.traffic_gen.step(mode=mode)
        original_logs = raw_logs.copy()
        
        # 3. Apply Mitigation Actions (Filtered Logs)
        processed_logs = self._apply_action(action, raw_logs)
        
        # 4. Update Internal State
        self._state.raw_logs.extend(processed_logs)
        
        # 5. Compute Reward
        reward = self.reward_engine.compute_reward(
            original_logs=original_logs,
            processed_logs=processed_logs,
            state=self._state
        )
        
        # Update aggregated stats with latest reward engine metrics
        self._state.aggregated_stats = self.reward_engine.get_metrics()
        
        # 6. Build Next Observation
        observation = self._build_observation(processed_logs)
        
        # 7. Check Terminal Condition
        self.is_done = self._state.current_step >= 300
        
        # 8. Compile Info
        info = {
            "step": self._state.current_step,
            "mode": mode,
            "total_attacks_blocked": self._state.aggregated_stats.get("blocked_attacks", 0)
        }
        
        return {
            "observation": observation,
            "reward": reward,
            "done": self.is_done,
            "info": info
        }

    def state(self) -> StateModel:
        """
        Accessor for the full internal environment state.
        Required for graders and debugging.
        """
        return self._state

    def _cleanup_expired_rules(self):
        """Removes mitigation rules whose duration has elapsed."""
        self._state.active_mitigations = [
            rule for rule in self._state.active_mitigations 
            if self._state.current_step < rule.get("expires_at", float('inf'))
        ]

    def _apply_action(self, action: ActionModel, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handles rule persistence and log filtering."""
        self._cleanup_expired_rules()

        if action.action_type not in {"noop", "clear_actions"}:
            params = action.parameters
            duration = params.get("duration", 60)
            self._state.active_mitigations.append({
                "type": action.action_type,
                "target": params.get("ip") or params.get("path") or params.get("target"),
                "expires_at": self._state.current_step + duration,
                "params": params
            })
        elif action.action_type == "clear_actions":
            self._state.active_mitigations = []

        # Application Logic Order: block -> rate limit -> challenge -> waf
        rule_priority = {"block_ip": 1, "rate_limit_ip": 2, "enable_challenge": 3, "waf_rule": 4}
        sorted_rules = sorted(self._state.active_mitigations, key=lambda x: rule_priority.get(x["type"], 99))

        filtered_logs = logs
        for rule in sorted_rules:
            rule_type, target, params = rule["type"], rule["target"], rule.get("params", {})
            if rule_type == "block_ip":
                filtered_logs = [l for l in filtered_logs if l["ip"] != target]
            elif rule_type == "rate_limit_ip":
                limit, count = params.get("limit", 10), 0
                new_logs = []
                for l in filtered_logs:
                    if l["ip"] == target:
                        count += 1
                        if count <= limit: new_logs.append(l)
                    else: new_logs.append(l)
                filtered_logs = new_logs
            elif rule_type == "waf_rule":
                field, pattern, act = params.get("field", "path"), params.get("pattern", ""), params.get("action", "block")
                if act == "block": filtered_logs = [l for l in filtered_logs if l.get(field) != pattern]
            elif rule_type == "enable_challenge":
                filtered_logs = [l for l in filtered_logs if not (l["ip"] == target and random.random() < 0.5)]
        
        return filtered_logs

    def _build_observation(self, logs: List[Dict[str, Any]]) -> ObservationModel:
        """Aggregates traffic logs into the observation schema."""
        traffic_summary, endpoint_summary, error_counts = {}, {}, {}
        for log in logs:
            ip, path, status = log["ip"], log["path"], log["status"]
            traffic_summary[ip] = traffic_summary.get(ip, 0) + 1
            endpoint_summary[path] = endpoint_summary.get(path, 0) + 1
            if status >= 400: error_counts[ip] = error_counts.get(ip, 0) + 1

        error_rates, anomaly_scores, VOLUME_THRESHOLD = {}, {}, 50.0
        for ip, count in traffic_summary.items():
            rate = error_counts.get(ip, 0) / count
            error_rates[ip] = rate
            anomaly_scores[ip] = min(1.0, (count / VOLUME_THRESHOLD) + rate)

        return ObservationModel(
            traffic_summary=traffic_summary,
            endpoint_summary=endpoint_summary,
            error_rates=error_rates,
            anomaly_scores=anomaly_scores,
            active_rules=self._state.active_mitigations,
            timestamp=self._state.current_step
        )

# --- Example Usage (Documentation) ---
# env = GatekeeperEnv()
# initial = await env.reset()
# result = await env.step(ActionModel(action_type="noop", parameters={}))
# print(f"Current Step Result: {result['reward']}")
