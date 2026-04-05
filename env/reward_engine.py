from typing import List, Dict, Any, Optional
from .models import StateModel

class RewardEngine:
    """
    Evaluates agent performance by comparing raw and filtered traffic logs.
    Provides dense, step-wise reward signals and tracks cumulative metrics.
    """

    def __init__(self):
        # Continuous Step Metrics
        self.total_requests = 0
        self.attack_requests = 0
        self.blocked_attacks = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.step_count = 0
        
        # Performance Tracking
        self.first_detection_step: Optional[int] = None

    def _is_attack(self, log: Dict[str, Any], state: StateModel) -> bool:
        """
        Heuristic to determine if a specific log entry represents an attack.
        """
        # Logic: Status 401/403 or if the IP is known to be part of a ground-truth attack
        status = log.get("status", 200)
        # Check status codes
        if status in {401, 403}:
            return True
        # Check if any global attack flags are active (Simplified for skeleton)
        # If any attack flag is true, we consider the log suspicious if it has certain qualities
        if any(state.attack_flags.values()):
            # If ddos is active, high frequency IPs are attacks (state-based ground truth)
            pass
        return False

    def compute_reward(self, original_logs: List[Dict[str, Any]], processed_logs: List[Dict[str, Any]], state: StateModel) -> float:
        """
        Calculates density-based reward for the current step.
        Compares original traffic vs what the WAF allowed through.
        """
        self.step_count = state.current_step
        
        tp, tn, fp, fn = 0, 0, 0, 0
        
        # Convert processed_logs to a multiset-like structure for efficient lookup
        # Since logs can be identical, we track counts
        remaining_logs = {}
        for log in processed_logs:
            log_key = (log["ip"], log["path"], log["status"])
            remaining_logs[log_key] = remaining_logs.get(log_key, 0) + 1

        for log in original_logs:
            self.total_requests += 1
            log_key = (log["ip"], log["path"], log["status"])
            is_atk = self._is_attack(log, state)
            
            if is_atk:
                self.attack_requests += 1
                # Was it blocked? (Not in remaining logs)
                if remaining_logs.get(log_key, 0) > 0:
                    fn += 1 # Attack request still present
                    self.false_negatives += 1
                    remaining_logs[log_key] -= 1
                else:
                    tp += 1 # Attack request removed
                    self.blocked_attacks += 1
            else:
                # Legit Request
                if remaining_logs.get(log_key, 0) > 0:
                    tn += 1 # Legit request allowed
                    remaining_logs[log_key] -= 1
                else:
                    fp += 1 # False Positive: Legit request blocked
                    self.false_positives += 1

        # --- Latency Bonus / Penalty ---
        latency_modifier = 0.0
        if tp > 0 and self.first_detection_step is None:
            self.first_detection_step = state.current_step
            if self.first_detection_step <= 5:
                latency_modifier = 3.0
            elif self.first_detection_step >= 30:
                latency_modifier = -2.0

        # --- Final Reward Calculation ---
        reward = (
            (tp * 1.0) +
            (tn * 0.5) -
            (fn * 5.0) -
            (fp * 10.0)
        )
        
        return reward + latency_modifier

    def get_metrics(self) -> Dict[str, Any]:
        """
        Summarizes performance metrics for grading.
        """
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

# --- Example Logic (Documentation) ---
# original_logs = [ {"ip": "1.1.1.1", "status": 401}, {"ip": "2.2.2.2", "status": 200} ]
# processed_logs = [ {"ip": "2.2.2.2", "status": 200} ]
# TP = 1, TN = 1 -> Reward = 1.5
