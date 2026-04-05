# 🚀 Gatekeeper — OpenEnv Cybersecurity Environment

## 🧠 Overview

Gatekeeper is a real-world OpenEnv-compatible reinforcement learning environment designed to train AI agents to defend web services against Denial of Service (DoS) and Distributed Denial of Service (DDoS) attacks.

Unlike toy simulations, Gatekeeper models realistic network traffic, attack patterns, and mitigation strategies used in production systems such as Web Application Firewalls (WAFs).

---

## 🎯 Motivation

Modern applications face constant threats from automated attacks:

* Brute force login attempts
* Volumetric DDoS traffic
* Slowloris attacks
* Credential stuffing

Existing RL environments lack realistic cybersecurity scenarios.

Gatekeeper fills this gap by providing:

* Real-time streaming traffic
* Structured decision-making
* Trade-offs between security and usability

---

## 🏗️ Environment Design

### ⏱️ Time Model

* 1 step = 1 second
* 1 episode = 300 steps (5 minutes simulated time)

### 📥 Observation Space

Each step returns structured traffic insights:

* Top IPs by request volume
* Requests per endpoint
* Error rates
* Suspicious activity signals
* Active mitigation rules

### 📤 Action Space

Agents can take the following actions:

| Action           | Description               |
| ---------------- | ------------------------- |
| rate_limit_ip    | Limit requests from an IP |
| block_ip         | Block malicious IP        |
| rate_limit_path  | Protect endpoints         |
| enable_challenge | Apply CAPTCHA             |
| add_waf_rule     | Pattern-based blocking    |
| whitelist_ip     | Allow trusted traffic     |
| clear_actions    | Remove restrictions       |

⚠️ Action budget: **Max 10 actions per episode**

---

## 🧮 Reward Function

### ✅ Positive Rewards

* Block attack traffic: +1
* Allow legitimate traffic: +0.5
* Early detection (<5s): +3
* Correct attack classification: +5

### ❌ Negative Rewards

* Miss attack: -5
* False positive (block legit user): -10
* Slow detection (>30s): -2
* Over-blocking penalties
* Wasted actions: -2

### 🏁 Episode Outcomes

* Success (>90% block & <1% false positives): +20
* Failure (<50% block): -15

---

## 🎮 Tasks & Difficulty

### 🟢 Task 1: Brute Force Attack

* Repeated login attempts from single IP
* Goal: detect and block

### 🟡 Task 2: Volumetric DDoS

* Sudden spike in traffic
* Goal: rate-limit efficiently

### 🔴 Task 3: Multi-Vector Attack

* Combination of attack types
* Goal: balance protection vs usability

---

## 📊 Grading System

Each task uses deterministic graders based on:

* Precision (correct blocks)
* Recall (attack coverage)
* Time-to-response
* False positive rate

Output score: **0.0 → 1.0**

---

## ⚙️ OpenEnv API

### `reset()`

Initializes environment and returns first observation

### `step(action)`

Returns:

* observation
* reward
* done
* info

### `state()`

Returns full internal environment state

---

## 🧪 Baseline Inference

Run baseline agent:

```bash
python inference.py
```

### Requirements:

Set environment variables:

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_token_here"
```

### Output Format

```
[START] ...
[STEP] ...
[END] ...
```

Strict format compliance is required for evaluation.

---

## 🐳 Setup & Installation

### 1. Clone Repository

```bash
git clone <repo-url>
cd gatekeeper
```

### 2. Build Docker Image

```bash
docker build -t gatekeeper-env .
```

### 3. Run Container

```bash
docker run -p 7860:7860 gatekeeper-env
```

---

## 🌐 Deployment (Hugging Face Spaces)

* Use Docker-based Space
* Tag: `openenv`
* Ensure endpoints:

  * `/reset`
  * `/step`

---

## 📁 Project Structure

```
/env/
  gatekeeper_env.py
  models.py
  traffic_generator.py
  reward_engine.py
  graders/

inference.py
openenv.yaml
Dockerfile
README.md
scripts/
```

---

## ✅ Validation Checklist

Before submission:

* HF Space responds to `/reset`
* Docker build passes
* `openenv validate` passes
* 3+ tasks with graders
* Inference script runs successfully

Run validator:

```bash
bash scripts/validate-submission.sh <hf_space_url>
```

---

## ⚠️ Constraints

* Max runtime: 20 minutes
* CPU: 2 vCPU
* Memory: 8GB

---

## 💡 Why Gatekeeper?

* Real-world cybersecurity relevance
* Complex decision-making environment
* Balanced reward design
* Deterministic evaluation
* Scalable for future research

---

## 🔮 Future Enhancements

* Adaptive adversarial attacks
* Multi-agent defense systems
* Integration with real traffic datasets

---

## 🤝 Contribution

Contributions are welcome! Improve attack models, reward strategies, or evaluation metrics.

---

## 📜 License

MIT License

---

## 🚀 Usage

To run the environment in a standalone inference loop:

```bash
pip install -r requirements.txt
python inference.py
```

To validate the environment against OpenEnv specs:

```bash
openenv validate openenv.yaml
```

---

## 🧭 Final Note

Gatekeeper is not just an environment — it's a battlefield where intelligence meets chaos, and only the most adaptive agents survive.
