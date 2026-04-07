import asyncio
import random
import logging
from typing import Dict, Any, Tuple, List, Optional
from .models import ObservationModel, ActionModel, StateModel
from .traffic_generator import TrafficGenerator
from .reward_engine import RewardEngine

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gatekeeper")

class GatekeeperEnv:
    """
    Highly-optimized OpenEnv for Cybersecurity simulation.
    Efficient Rule Filtering, Structured Logging, and Step Orchestration.
    """

    MAX_STEPS = 300

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.traffic_gen = TrafficGenerator(seed=seed)
        self.reward_engine = RewardEngine()
        self._state: Optional[StateModel] = None
        self.is_done = False

    async def reset(self) -> Dict[str, Any]:
        """Resets the simulation and returns initial observation."""
        try:
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
            
            # Use normal mode for initial bootstrap logs
            initial_logs = self.traffic_gen.step(mode="normal")
            observation = self._build_observation(initial_logs)
            
            return {
                "observation": observation,
                "reward": 0.0,
                "done": False,
                "info": {"step": 0, "mode": "normal"}
            }
        except Exception as e:
            logger.error(f"Failed to reset environment: {e}")
            raise

    def _get_current_mode(self) -> str:
        """Determines traffic phase based on stepwise progression."""
        step = self._state.current_step
        if step < 100: return "normal"
        if step < 200: return "bruteforce"
        if step < 250: return "ddos"
        return "multivector"

    async def step(self, action: ActionModel) -> Dict[str, Any]:
        """Execution: Traffic -> Filter -> Reward -> Obs."""
        if self._state is None:
            raise RuntimeError("Environment has not been reset().")

        try:
            # 1. Increment Step
            self._state.current_step += 1
            mode = self._get_current_mode()
            
            # Log key stepwise metadata
            logger.info(f"Step {self._state.current_step} | Mode: {mode}")
            logger.info(f"Action Recv: {action.action_type}")
            
            # 2. Get Raw Traffic
            raw_logs = self.traffic_gen.step(mode=mode)
            if not raw_logs:
                # Handle edge case for empty traffic step
                return {
                    "observation": self._build_observation([]),
                    "reward": 0.0,
                    "done": self.is_done,
                    "info": {"step": self._state.current_step, "mode": mode}
                }
            
            # Use shallow copy for efficiency
            original_logs = list(raw_logs)
            
            # 3. Filter Traffic via Action Engine
            processed_logs = self._apply_action(action, raw_logs)
            
            # 4. State Update
            self._state.raw_logs.extend(processed_logs)
            self._state.attack_flags = {
                "bruteforce": mode == "bruteforce",
                "ddos": mode == "ddos",
                "multivector": mode == "multivector"
            }
            
            # 5. Reward Computation
            reward = self.reward_engine.compute_reward(
                original_logs=original_logs,
                processed_logs=processed_logs,
                state=self._state
            )
            logger.info(f"Step Reward: {reward}")
            
            # Update metric stats
            self._state.aggregated_stats = self.reward_engine.get_metrics()
            
            # 6. Build Feedback
            observation = self._build_observation(processed_logs)
            self.is_done = self._state.current_step >= self.MAX_STEPS
            
            return {
                "observation": observation,
                "reward": reward,
                "done": self.is_done,
                "info": {"step": self._state.current_step, "mode": mode}
            }
        except Exception as e:
            logger.error(f"Error in simulation step {self._state.current_step}: {e}")
            raise

    def state(self) -> StateModel:
        """Returns internal ground truth state."""
        return self._state

    def _cleanup_expired_rules(self):
        """Removes expired mitigation policies."""
        current = self._state.current_step
        self._state.active_mitigations = [
            r for r in self._state.active_mitigations if r["expires_at"] > current
        ]

    def _apply_action(self, action: ActionModel, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Orchestrates rule management and O(N) log filtering."""
        self._cleanup_expired_rules()

        # Handle new action arrival
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

        # Rules Priority: Block > Rate Limit > Challenge > WAF
        rule_priority = {"block_ip": 1, "rate_limit_ip": 2, "enable_challenge": 3, "waf_rule": 4}
        sorted_rules = sorted(self._state.active_mitigations, key=lambda x: rule_priority.get(x["type"], 99))

        # Pre-process rules for faster filtering
        # Optimize shared IPs for block checks
        blocked_ips = {r["target"] for r in sorted_rules if r["type"] == "block_ip"}
        # Map rate limits
        rate_limits = {r["target"]: r["params"].get("limit", 10) for r in sorted_rules if r["type"] == "rate_limit_ip"}

        filtered_logs = logs
        for rule in sorted_rules:
            r_type, target, params = rule["type"], rule["target"], rule.get("params", {})
            
            if r_type == "block_ip":
                # IPs are checked against the precompiled set for O(1) lookup
                filtered_logs = [l for l in filtered_logs if l["ip"] not in blocked_ips]
            elif r_type == "rate_limit_ip":
                # Track limiters locally per IP
                limit, count = rate_limits.get(target, 10), 0
                new_logs = []
                for l in filtered_logs:
                    if l["ip"] == target:
                        count += 1
                        if count <= limit: new_logs.append(l)
                    else:
                        new_logs.append(l)
                filtered_logs = new_logs
            elif r_type == "waf_rule":
                f, p, act = params.get("field", "path"), params.get("pattern", ""), params.get("action", "block")
                if act == "block":
                    filtered_logs = [l for l in filtered_logs if l.get(f) != p]
            elif r_type == "enable_challenge":
                # Simulated probabilistic challenge filter
                filtered_logs = [l for l in filtered_logs if not (l["ip"] == target and random.random() < 0.5)]
        
        return filtered_logs

    def _build_observation(self, logs: List[Dict[str, Any]]) -> ObservationModel:
        """Efficiently compiles aggregation stats into an ObservationModel."""
        from collections import Counter
        # O(N) counts for both IPs and paths
        ip_counts = Counter(l["ip"] for l in logs)
        path_counts = Counter(l["path"] for l in logs)
        error_counts = Counter(l["ip"] for l in logs if l["status"] >= 400)

        error_rates = {ip: (error_counts[ip] / c) for ip, c in ip_counts.items()}
        # Threshold for volume-based anomalies
        V_THR = 50.0
        anomaly_scores = {ip: min(1.0, (c / V_THR) + error_rates.get(ip, 0)) for ip, c in ip_counts.items()}

        return ObservationModel(
            traffic_summary=dict(ip_counts),
            endpoint_summary=dict(path_counts),
            error_rates=error_rates,
            anomaly_scores=anomaly_scores,
            active_rules=list(self._state.active_mitigations),
            timestamp=self._state.current_step
        )
