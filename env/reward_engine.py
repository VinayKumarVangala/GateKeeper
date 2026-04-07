from typing import List, Dict, Any, Optional
from collections import Counter
from .models import StateModel

class RewardEngine:
    """
    Evaluates agent performance with O(n) efficiency and precision.
    Tracks performance metrics and computes stepwise rewards.
    """

    def __init__(self):
        # Stepwise accumulation metrics
        self.total_requests = 0
        self.attack_requests = 0
        self.blocked_attacks = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.step_count = 0
        
        # State tracking
        self.first_detection_step: Optional[int] = None

    def _is_attack(self, log: Dict[str, Any], state: StateModel) -> bool:
        """Determines if a log entry describes an attack."""
        status = log.get("status", 200)
        # Direct check for common attack indicators
        if status in {401, 403}:
            return True
        # Check global state flags (simplified logic)
        if any(state.attack_flags.values()):
            # Potentially implement IP-based ground truth comparison
            pass
        return False

    def compute_reward(self, original_logs: List[Dict[str, Any]], processed_logs: List[Dict[str, Any]], state: StateModel) -> float:
        """
        Calculates Step-wise reward with optimized Counters (O(N) total).
        """
        self.step_count = state.current_step
        tp, tn, fp, fn = 0, 0, 0, 0
        
        # O(N) counts for remaining logs
        remaining_counter = Counter((l["ip"], l["path"], l["status"]) for l in processed_logs)

        # O(N) traversal of original logs
        for log in original_logs:
            self.total_requests += 1
            log_key = (log["ip"], log["path"], log["status"])
            is_atk = self._is_attack(log, state)
            
            if is_atk:
                self.attack_requests += 1
                if remaining_counter[log_key] > 0:
                    fn += 1 # Attack request still present
                    self.false_negatives += 1
                    remaining_counter[log_key] -= 1
                else:
                    tp += 1 # Attack request blocked successfully
                    self.blocked_attacks += 1
            else:
                if remaining_counter[log_key] > 0:
                    tn += 1 # Legit request allowed
                    remaining_counter[log_key] -= 1
                else:
                    fp += 1 # Legit request blocked (False Positive)
                    self.false_positives += 1

        # --- Latency Bonus / Penalty ---
        # Only applies once at the point of first mitigation
        latency_modifier = 0.0
        if tp > 0 and self.first_detection_step is None:
            self.first_detection_step = state.current_step
            if self.first_detection_step <= 5:
                latency_modifier = 3.0
            elif self.first_detection_step >= 30:
                latency_modifier = -2.0

        # --- Final Reward ---
        reward = (tp * 1.0) + (tn * 0.5) - (fn * 5.0) - (fp * 10.0)
        return reward + latency_modifier

    def get_metrics(self) -> Dict[str, Any]:
        """Summarizes performance metrics for evaluation."""
        precision = self.blocked_attacks / (self.blocked_attacks + self.false_positives) if (self.blocked_attacks + self.false_positives) > 0 else 0.0
        recall = self.blocked_attacks / self.attack_requests if self.attack_requests > 0 else 0.0
        
        return {
            "total_requests": self.total_requests,
            "attack_requests": self.attack_requests,
            "blocked_attacks": self.blocked_attacks,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": precision,
            "recall": recall,
            "first_detection_step": self.first_detection_step
        }
