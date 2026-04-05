from typing import List, Any

def evaluate(state_history: List[Any]) -> float:
    """
    Evaluates agent performance on Multi-Vector Attack Mitigation.
    Focuses on:
    - Balanced defense across all attack streams.
    - Consistency over full episode.
    """
    if not state_history:
        return 0.0

    last_state = state_history[-1]
    stats = last_state.aggregated_stats

    # Use F1-based score for Multi-vector to penalize failure on any one vector
    precision = stats.get("precision", 0.0)
    recall = stats.get("recall", 0.0)
    
    # 2 * P * R / (P + R)
    f1_score = (2.0 * precision * recall) / (precision + recall + 1e-9)
    
    # Penalty for false positives (most critical in multi-vector)
    fp_penalty = 0.0
    if stats.get("false_positives", 0) > 100:
        fp_penalty = 0.2 # -20% score for high false positive rates

    final_score = f1_score - fp_penalty
    return min(1.0, max(0.0, final_score))
