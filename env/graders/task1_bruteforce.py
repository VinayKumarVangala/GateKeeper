from typing import List, Any

def evaluate(state_history: List[Any]) -> float:
    """
    Evaluates agent performance on Brute Force Mitigation.
    Focuses on:
    - High Precision (no false blocks)
    - High Recall (all attacks blocked)
    - Response Time < 10s
    """
    if not state_history:
        return 0.0

    last_state = state_history[-1]
    stats = last_state.aggregated_stats

    precision = stats.get("precision", 0.0)
    recall = stats.get("recall", 0.0)
    first_detection = stats.get("first_detection_step", 300)

    # 1. Base Score from Precision and Recall
    # F1-like harmonic mean or weighted average
    base_score = (precision * 0.4) + (recall * 0.4)

    # 2. Response Time Bonus (Total 0.2)
    time_bonus = 0.0
    if recall > 0.5: # Only give bonus if they actually caught some
        if first_detection <= 5:
            time_bonus = 0.2
        elif first_detection <= 20:
            time_bonus = 0.1
        elif first_detection <= 50:
            time_bonus = 0.05

    final_score = base_score + time_bonus
    return min(1.0, max(0.0, final_score))
