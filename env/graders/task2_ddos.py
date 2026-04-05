from typing import List, Any

def evaluate(state_history: List[Any]) -> float:
    """
    Evaluates agent performance on Volumetric DDoS Mitigation.
    Focuses on:
    - High Recall (blocking large volume attacks)
    - High Precision (ensuring legit traffic flow during attack)
    """
    if not state_history:
        return 0.0

    last_state = state_history[-1]
    stats = last_state.aggregated_stats

    precision = stats.get("precision", 0.0) # Correctness of blocks
    recall = stats.get("recall", 0.0)       # Coverage of ddos stream
    
    # In DDoS, Precision is harder due to collateral damage
    # We weight Precision slightly higher to ensure usability
    final_score = (precision * 0.6) + (recall * 0.4)
    
    # Bonus for early action (> 1000 requests blocked early)
    if stats.get("blocked_attacks", 0) > 1000:
        final_score += 0.05

    return min(1.0, max(0.0, final_score))
