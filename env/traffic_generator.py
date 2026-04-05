import random
from typing import List, Dict, Any, Optional

class TrafficGenerator:
    """
    Simulates realistic web traffic scenarios for the Gatekeeper environment.
    Supports normal operation and various attack vectors (Brute Force, DDoS, Multi-vector).
    """

    def __init__(self, seed: int = 42):
        """
        Initialize the generator with a fixed seed for deterministic reproducibility.
        """
        self.seed = seed
        self.random = random.Random(seed)
        self.current_step = 0
        
        # Pre-generate some known IPs to simulate recurring users/attackers
        self.legit_ips = [self._generate_ip() for _ in range(50)]
        self.attacker_ips = [self._generate_ip() for _ in range(200)]
        
        # Common Endpoints
        self.endpoints = ["/", "/home", "/login", "/api/data", "/settings", "/profile"]
        self.status_codes = [200, 201, 401, 403, 404, 500]

    def _generate_ip(self) -> str:
        """Helper to generate a random IPv4 address string."""
        return f"{self.random.randint(1, 255)}.{self.random.randint(0, 255)}.{self.random.randint(0, 255)}.{self.random.randint(1, 254)}"

    def _choose_endpoint(self, focus: Optional[str] = None) -> str:
        """Selects an endpoint, optionally focusing on a specific one for attacks."""
        if focus and self.random.random() < 0.8:  # 80% weight to focused endpoint
            return focus
        return self.random.choice(self.endpoints)

    def _generate_status_code(self, mode: str = "normal") -> int:
        """Generates HTTP status codes based on the traffic mode."""
        if mode == "normal":
            # 95% success, 5% occasional errors
            return self.random.choices([200, 404, 500], weights=[95, 4, 1])[0]
        elif mode == "bruteforce":
            # High failure rate for unauthorized access
            return self.random.choices([401, 403, 200], weights=[80, 15, 5])[0]
        return 200

    def generate_legit_traffic(self) -> List[Dict[str, Any]]:
        """
        Simulates low-to-moderate volume legitimate user traffic.
        """
        logs = []
        num_requests = self.random.randint(5, 15)
        
        for _ in range(num_requests):
            ip = self.random.choice(self.legit_ips)
            logs.append({
                "ip": ip,
                "path": self.random.choice(self.endpoints[:4]), # Focus on main pages
                "status": self._generate_status_code("normal"),
                "timestamp": self.current_step
            })
        return logs

    def generate_bruteforce_attack(self) -> List[Dict[str, Any]]:
        """
        Simulates a targeted brute force attack on the /login endpoint.
        Uses 1-3 fixed attacker IPs with high frequency.
        """
        logs = []
        num_attackers = self.random.randint(1, 3)
        attackers = self.attacker_ips[:num_attackers]
        
        # Each attacker sends many requests per second
        for ip in attackers:
            num_requests = self.random.randint(20, 50)
            for _ in range(num_requests):
                logs.append({
                    "ip": ip,
                    "path": "/login",
                    "status": self._generate_status_code("bruteforce"),
                    "timestamp": self.current_step
                })
        return logs

    def generate_ddos_attack(self) -> List[Dict[str, Any]]:
        """
        Simulates a volumetric DDoS attack involving hundreds of distinct IPs.
        """
        logs = []
        # Large pool of attackers
        num_attack_ips = self.random.randint(50, 150)
        attackers = self.random.sample(self.attacker_ips, num_attack_ips)
        
        for ip in attackers:
            # Each IP sends a smaller burst, but total volume is high
            num_requests = self.random.randint(5, 10)
            for _ in range(num_requests):
                logs.append({
                    "ip": ip,
                    "path": self._choose_endpoint(),
                    "status": self.random.choice([200, 500, 503] if self.random.random() > 0.5 else [200]),
                    "timestamp": self.current_step
                })
        return logs

    def generate_multivector_attack(self) -> List[Dict[str, Any]]:
        """
        Simulates a complex multi-vector attack combining DDoS and targeted Brute Force.
        """
        logs = []
        # Add Legit Traffic
        logs.extend(self.generate_legit_traffic())
        # Add Brute Force (Targeted)
        logs.extend(self.generate_bruteforce_attack())
        # Add DDoS (Volumetric)
        logs.extend(self.generate_ddos_attack())
        
        # Scramble to ensure logs are interleaved
        self.random.shuffle(logs)
        return logs

    def step(self, mode: str = "normal") -> List[Dict[str, Any]]:
        """
        Advances the simulation by one step and generates traffic logs for the specified mode.
        Modes: 'normal', 'bruteforce', 'ddos', 'multivector'
        """
        self.current_step += 1
        
        if mode == "normal":
            return self.generate_legit_traffic()
        elif mode == "bruteforce":
            # Mix some legit in with the attack
            return self.generate_legit_traffic() + self.generate_bruteforce_attack()
        elif mode == "ddos":
            return self.generate_legit_traffic() + self.generate_ddos_attack()
        elif mode == "multivector":
            return self.generate_multivector_attack()
        
        return self.generate_legit_traffic()

# --- Example Output (Documentation) ---
# [
#   {"ip": "192.168.1.10", "path": "/login", "status": 401, "timestamp": 12},
#   {"ip": "10.0.0.5", "path": "/api/data", "status": 200, "timestamp": 12}
# ]
