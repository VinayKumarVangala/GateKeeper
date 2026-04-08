from typing import List, Any

def evaluate(state_history: List[Any]) -> float:
    """
    Evaluates agent performance on Volumetric DDoS Mitigation.
    Standardized OpenEnv grader logic.
    """
    if not state_history:
        return 0.01

    last_state = state_history[-1]
    stats = getattr(last_state, "aggregated_stats", {})
    if not stats and isinstance(last_state, dict):
        stats = last_state.get("aggregated_stats", {})

    tp = stats.get("blocked_attacks", 0)
    fp = stats.get("false_positives", 0)
    fn = stats.get("false_negatives", 0)
    first_detection = stats.get("first_detection_step")

    # Core scoring logic
    precision = tp / (tp + fp + 1e-6)
    recall = tp / (tp + fn + 1e-6)
    score = 0.5 * precision + 0.5 * recall

    # Response time bonus/penalty
    if first_detection is not None:
        if first_detection < 5:
            score += 0.05
        elif first_detection > 30:
            score -= 0.05

    # Strict clamping to (0, 1) exclusive
    return max(0.01, min(score, 0.99))
