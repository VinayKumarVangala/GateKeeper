# 🛡️ Gatekeeper App Manual

Welcome to the **Gatekeeper OpenEnv Cybersecurity Demo** deployed on Hugging Face Spaces! This interactive guide describes the functionalities available to you in the UI and how to interact with the real-time simulation.

## 🎯 Purpose
The Gatekeeper visual demo allows you to manually walk through a Web Application Firewall (WAF) simulation, which is typically navigated autonomously by Reinforcement Learning (RL) agents. Your goal is to safeguard the simulated API from various cyber-attacks (like DoS, DDoS, and Brute Force) by deploying precise countermeasures.

---

## 🖥️ User Interface Overview

### 1. Security Control Panel 📡
This section is your primary interaction hub, simulating the command center of a network security engineer.

- **Action Type (Dropdown):** Choose which WAF rule or mitigation policy you want to dispatch. 
  - *Tip:* Use `noop` (No Operation) to let traffic flow normally and collect metrics. Use `block_ip` or `rate_limit_ip` when you spot anomalies.
- **Target Entity (Textbox):** Provide the specific IP address (e.g., `10.0.0.5`) or path (e.g., `/api/login`) exactly as it appears in the active traffic logs to target your action.
- **▶ Step Environment (Button):** Executes your chosen action and advances the server traffic simulation by one single time-step (typically 1 second of traffic).
- **🔄 Reset Episode (Button):** Wipes the current WAF rules, resets all traffic generators, and starts a fresh attack scenario from step 0. 

### 2. Observation & Reward Dashboard 📊
When you execute a step, the simulation computes the next chunk of logs and evaluates your action.

- **Observation Data:** Displays real-time metrics including:
  - `traffic_summary`: Total requests from specific IPs.
  - `endpoint_summary`: The volume of requests hitting specific API paths.
  - `error_rates`: Ratio of failed or malformed requests.
  - `anomaly_scores`: AI-computed suspicion metrics tracking unusual access patterns.
  - `active_rules`: All mitigation rules currently active in the firewall.
- **Reward Signal:** The numeric feedback score. Positive scores indicate successful mitigation of an attack or allowing legitimate users. Negative scores indicate false positives or allowing attacks to succeed.

### 3. Internal State Dump ⚙️
This tab provides a transparent, raw peek at the underlying `GatekeeperEnv` state properties. It serves as ground-truth for the system and includes:
- Ongoing attack flags.
- Buffer lists of incoming packet properties.
- Current total timestep context.

---

## 📝 Step-by-Step Scenario Example

1. **Start Fresh:** Click **🔄 Reset Episode** to initialize the environment.
2. **Observe Traffic:** Ensure **Action Type** is set to `noop` and click **▶ Step Environment** a few times. Switch to the *Observation & Reward* tab to view the `traffic_summary` and `anomaly_scores`.
3. **Detect Malicious IP:** Notice an IP (e.g., `192.168.1.100`) generating disproportionate requests and a soaring anomaly score.
4. **Deploy Mitigation:** 
   - Change **Action Type** to `block_ip`.
   - Enter `192.168.1.100` into the **Target Entity** field.
   - Click **▶ Step Environment**.
5. **Verify:** You should receive a positive reward for correctly mitigating the threat. Check the `active_rules` array in the Observation JSON to verify the firewall rule was correctly registered.

## 🔗 Seamless OpenEnv Integration
Behind this visual dashboard, the very same computational engine is fully compliant with the `openenv-core` SDK, meaning an RL AI agent interacts with the exact same step-by-step logic that you just did!
