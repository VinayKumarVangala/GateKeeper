import random
import numpy as np
from typing import List, Dict, Any, Optional

# Set seeds globally for deterministic simulation
random.seed(42)
np.random.seed(42)

class TrafficGenerator:
    """
    Simulates realistic web traffic scenarios for the Gatekeeper environment.
    Optimized for performance and determinism.
    """

    MAX_LOGS_PER_STEP = 200

    def __init__(self, seed: int = 42):
        """
        Initialize the generator with a fixed seed for deterministic reproducibility.
        """
        self.seed = seed
        self.random = random.Random(seed)
        self.current_step = 0
        
        # Pre-generate some known IPs to simulate recurring users/attackers
        self.legit_ips = list({self._generate_ip() for _ in range(50)})
        self.attacker_ips = list({self._generate_ip() for _ in range(200)})
        
        # Common Endpoints
        self.endpoints = ["/", "/home", "/login", "/api/data", "/settings", "/profile"]
        self.status_codes = [200, 201, 401, 403, 404, 500]

    def _generate_ip(self) -> str:
        """Helper to generate a random IPv4 address string."""
        return f"{self.random.randint(1, 255)}.{self.random.randint(0, 255)}.{self.random.randint(0, 255)}.{self.random.randint(1, 254)}"

    def _choose_endpoint(self, focus: Optional[str] = None) -> str:
        """Selects an endpoint using simple probabilistic patterns."""
        if focus and self.random.random() < 0.8:
            return focus
        return self.random.choice(self.endpoints)

    def _generate_status_code(self, mode: str = "normal") -> int:
        """Generates HTTP status codes based on the traffic mode."""
        if mode == "normal":
            return self.random.choices([200, 404, 500], weights=[95, 4, 1])[0]
        elif mode == "bruteforce":
            return self.random.choices([401, 403, 200], weights=[80, 15, 5])[0]
        return 200

    def generate_legit_traffic(self) -> List[Dict[str, Any]]:
        """Simulates low-to-moderate volume legitimate user traffic."""
        num_requests = self.random.randint(5, 15)
        logs = [
            {
                "ip": self.random.choice(self.legit_ips),
                "path": self.random.choice(self.endpoints[:4]),
                "status": self._generate_status_code("normal"),
                "timestamp": self.current_step
            }
            for _ in range(num_requests)
        ]
        return logs

    def generate_bruteforce_attack(self) -> List[Dict[str, Any]]:
        """Simulates a targeted brute force attack on /login."""
        num_attackers = self.random.randint(1, 3)
        attackers = self.attacker_ips[:num_attackers]
        logs = []
        
        for ip in attackers:
            num_requests = self.random.randint(20, 50)
            for _ in range(num_requests):
                logs.append({
                    "ip": ip,
                    "path": "/login",
                    "status": self._generate_status_code("bruteforce"),
                    "timestamp": self.current_step
                })
        return logs[:self.MAX_LOGS_PER_STEP]

    def generate_ddos_attack(self) -> List[Dict[str, Any]]:
        """Simulates a volumetric DDoS attack."""
        num_attack_ips = self.random.randint(50, 100)
        attackers = self.random.sample(self.attacker_ips, num_attack_ips)
        logs = []
        
        for ip in attackers:
            num_requests = self.random.randint(2, 5)
            for _ in range(num_requests):
                logs.append({
                    "ip": ip,
                    "path": self._choose_endpoint(),
                    "status": self.random.choice([200, 500, 503]),
                    "timestamp": self.current_step
                })
        return logs[:self.MAX_LOGS_PER_STEP]

    def generate_multivector_attack(self) -> List[Dict[str, Any]]:
        """Simulates complex interleaved attacks."""
        logs = []
        logs.extend(self.generate_legit_traffic())
        logs.extend(self.generate_bruteforce_attack())
        logs.extend(self.generate_ddos_attack())
        
        self.random.shuffle(logs)
        return logs[:self.MAX_LOGS_PER_STEP]

    def step(self, mode: str = "normal") -> List[Dict[str, Any]]:
        """Advances simulation and generates logs constrained by MAX_LOGS_PER_STEP."""
        self.current_step += 1
        
        if mode == "normal":
            logs = self.generate_legit_traffic()
        elif mode == "bruteforce":
            logs = self.generate_legit_traffic() + self.generate_bruteforce_attack()
        elif mode == "ddos":
            logs = self.generate_legit_traffic() + self.generate_ddos_attack()
        elif mode == "multivector":
            logs = self.generate_multivector_attack()
        else:
            logs = self.generate_legit_traffic()
            
        return logs[:self.MAX_LOGS_PER_STEP]
