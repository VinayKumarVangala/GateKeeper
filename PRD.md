# 📘 PRD.md — Gatekeeper (OpenEnv Environment)

## 1. Overview

**Product Name:** Gatekeeper
**Category:** OpenEnv RL Environment
**Domain:** Cybersecurity (DoS / DDoS Prevention)

Gatekeeper is a real-world simulation environment where an AI agent learns to defend a web service against denial-of-service attacks by analyzing streaming network logs and taking preventive actions.

The system mimics production-grade traffic patterns, attack vectors, and mitigation strategies, allowing agents to learn decision-making under uncertainty, time pressure, and trade-offs between security and usability.

---

## 2. Goals & Success Criteria

### 🎯 Primary Goals

* Build a **real-world usable RL environment** for cybersecurity defense
* Ensure **strict OpenEnv compliance**
* Enable **progressive learning via multi-difficulty tasks**
* Provide **deterministic, reproducible evaluation**

### 📊 Success Metrics

* ≥ 90% attack mitigation (true positives)
* ≤ 1% false positives
* Fast response time (< 5 seconds detection)
* Baseline reproducibility across runs

---

## 3. System Architecture

### 🏗️ High-Level Architecture

```
+----------------------+
| Traffic Generator    |
| (Legit + Attack)     |
+----------+-----------+
           |
           v
+----------------------+
| State Builder        |
| (Aggregation Engine) |
+----------+-----------+
           |
           v
+----------------------+
| OpenEnv Interface    |
| step/reset/state     |
+----------+-----------+
           |
           v
+----------------------+
| Agent (LLM/RL)       |
+----------+-----------+
           |
           v
+----------------------+
| Action Executor      |
| (WAF Simulator)      |
+----------+-----------+
           |
           v
+----------------------+
| Reward Engine        |
+----------------------+
```

---

## 4. Core Components

### 4.1 Traffic Generator

* Simulates real-world traffic
* Mix of:

  * Legitimate users
  * Attack patterns (Brute Force, DDoS, Slowloris, etc.)
* Time-based streaming (1 step = 1 second)

### 4.2 State Builder

* Aggregates logs into structured observations
* Outputs:

  * Request counts per IP/path
  * Error rates
  * Anomaly scores
  * Active mitigations

### 4.3 OpenEnv Interface

#### Functions:

* `reset()` → Initializes clean environment state
* `step(action)` → Executes action, returns:

  * observation
  * reward
  * done
  * info
* `state()` → Returns internal state snapshot

#### Models:

* Observation (Pydantic)
* Action (Pydantic)
* Reward (float)

---

## 5. Action Space

| Action           | Description             |
| ---------------- | ----------------------- |
| rate_limit_ip    | Limit requests from IP  |
| block_ip         | Block IP                |
| rate_limit_path  | Protect endpoint        |
| enable_challenge | Add CAPTCHA             |
| add_waf_rule     | Pattern-based filtering |
| whitelist_ip     | Trust traffic           |
| clear_actions    | Remove restrictions     |

**Constraint:** Max 10 actions per episode

---

## 6. Observation Space

Structured JSON-like state:

* Top IPs by traffic
* Request rate per endpoint
* Error ratios
* Suspicious patterns
* Active rules

---

## 7. Reward Design

### Positive Signals

* Block attack: +1
* Allow legitimate: +0.5
* Early detection: +3
* Correct classification: +5

### Negative Signals

* Miss attack: -5
* False positive: -10
* Slow detection: -2
* Over-blocking: small penalties
* Random/wasted actions: -2

### Episode Rewards

* Success bonus: +20
* Failure penalty: -15

---

## 8. Tasks & Difficulty Levels

### Task 1: Brute Force Detection (Easy)

* Pattern: repeated login attempts
* Goal: detect and block IP

### Task 2: Volumetric DDoS (Medium)

* Pattern: high traffic spike
* Goal: rate limit effectively

### Task 3: Multi-vector Attack (Hard)

* Pattern: combination of attacks
* Goal: balance blocking vs usability

---

## 9. Grader Design

Each task includes deterministic graders:

### Metrics:

* Precision
* Recall
* Time-to-block
* False positive rate

### Output:

* Score ∈ [0, 1]

---

## 10. Implementation Plan

### 🧰 Tech Stack

| Layer           | Technology          |
| --------------- | ------------------- |
| Core Env        | Python              |
| API Models      | Pydantic            |
| Simulation      | NumPy / Pandas      |
| OpenEnv SDK     | openenv-core        |
| Container       | Docker              |
| Deployment      | Hugging Face Spaces |
| LLM Interaction | OpenAI Client       |

---

## 11. Workflow (How Everything Runs)

### 🔄 Episode Flow

1. `reset()` initializes traffic and state
2. Agent receives observation
3. Agent selects action
4. `step(action)` executed
5. Traffic processed + rules applied
6. Reward calculated
7. Loop continues until 300 steps

---

## 12. Baseline Inference

* Script: `inference.py`
* Uses OpenAI client
* Logs:

  * [START]
  * [STEP]
  * [END]

### Constraints:

* Runtime < 20 min
* Deterministic outputs

---

## 13. Deployment Plan

### Docker

* Build environment image
* Expose API endpoints

### Hugging Face Space

* Container-based deployment
* Endpoint:

  * `/reset`
  * `/step`

---

## 14. Phases of Development

### Phase 1: Foundation

* Setup OpenEnv structure
* Define models
* Basic environment loop

### Phase 2: Simulation Engine

* Build traffic generator
* Implement attack patterns

### Phase 3: Actions & Rules

* Implement WAF logic
* Apply mitigation effects

### Phase 4: Reward & Graders

* Add scoring logic
* Validate determinism

### Phase 5: Baseline Agent

* Implement inference script
* Logging compliance

### Phase 6: Deployment

* Dockerize
* Deploy to HF Space

### Phase 7: Validation

* Run validator script
* Fix compliance issues

---

## 15. Repository Structure

```
/project-root
│── env/
│   ├── gatekeeper_env.py
│   ├── models.py
│   ├── traffic_generator.py
│   ├── reward_engine.py
│   └── graders/
│
│── inference.py
│── openenv.yaml
│── Dockerfile
│── README.md
│── scripts/
│   └── validate-submission.sh
```

---

## 16. Risk & Constraints

### Risks

* Over-complex simulation → slow runtime
* Non-deterministic grading
* Reward hacking by agent

### Constraints

* CPU: 2 vCPU
* Memory: 8GB
* Runtime < 20 min

---

## 17. Future Enhancements

* Adaptive adversarial attacks
* Multi-agent defense systems
* Reinforcement learning benchmarks

---

## 18. Conclusion

Gatekeeper is designed to bridge the gap between RL research and real-world cybersecurity. By combining structured environments, meaningful rewards, and deterministic evaluation, it creates a powerful benchmark for training and evaluating intelligent agents in high-stakes decision-making systems.
