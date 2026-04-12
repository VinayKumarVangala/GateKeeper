---
title: Gatekeeper Env
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
base_path: /
---

# 🛡️ Gatekeeper OpenEnv Environment

Gatekeeper is a real-world simulation environment where an AI agent learns to defend a web service against denial-of-service (DoS) and volumetric attacks by analyzing streaming network logs and taking preventive actions. 

This repository is compliant with **OpenEnv** standards and designed for RL agent evaluations and benchmarks in the cybersecurity domain. 

## ✨ Features
- Simulates Brute Force, DDoS, and Multi-vector attacks in real-time.
- Strict OpenEnv compliance with step/reset semantics.
- Progressive difficulty levels (Easy, Medium, Hard).
- Deterministic task graders evaluating precision, recall, and time-to-mitigate.
- Built-in WAF (Web Application Firewall) simulation with action space (block IP, rate limit, challenge).
- Interactive **Gradio Web Demo** available on Hugging Face Spaces.

## 📂 File Structure

```
.
├── env/
│   ├── gatekeeper_env.py    # Core OpenEnv environment logic
│   ├── models.py            # Pydantic schemas for Observation/Action/State
│   ├── traffic_generator.py # Simulates legitimate and attack traffic
│   ├── reward_engine.py     # dense reward computation logic
│   ├── server.py            # FastAPI + Gradio server for deployment
│   └── graders/             # Deterministic task evaluators
│       ├── task1_bruteforce.py
│       ├── task2_ddos.py
│       └── task3_multivector.py
├── openenv.yaml             # OpenEnv spec configuration (tasks, schemas)
├── inference.py             # Baseline LLM inference/evaluation script
├── requirements.txt         # Project dependencies
├── Dockerfile               # Production Docker definition
├── PRD.md                   # Product Requirements Document
├── IMPLEMENTATIONS.md       # Development implementation breakdown
└── README.md                # This file
```

## 🚀 Running Locally

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the API & UI Server:**
   ```bash
   python -m uvicorn env.server:app --host 0.0.0.0 --port 7860
   ```
   *Visit `http://localhost:7860/` to access the interactive Gradio demo.*

3. **Run Inference Benchmark:**
   ```bash
   python inference.py
   ```

## 🌐 Deployed on Hugging Face Spaces

This environment is fully Dockerized and deployed via Hugging Face. When visiting the Space, you will be greeted by an interactive application that demonstrates the work done:
- Select an action (e.g., `block_ip`, `rate_limit_path`).
- Submit to see the internal environment state evolve and observe the reward signals.

## 📝 Compliance
- All evaluation scores are mathematically normalized strictly within `(0.0, 1.0)`.
- Implements 3 unique task graders properly validated against the `openenv-core` specification.