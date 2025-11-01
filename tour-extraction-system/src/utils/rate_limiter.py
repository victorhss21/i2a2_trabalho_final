"""
Controle de rate limit thread-safe para APIs.
"""
import time
import threading


class RateLimiter:
    """Controle de rate limit para APIs"""
    
    def __init__(self, requests_per_minute: int):
        self.rate_limit = requests_per_minute
        self.timestamps = []
        self.lock = threading.Lock()
    
    def wait(self):
        """Aguarda até que seja seguro fazer nova requisição"""
        with self.lock:
            now = time.time()
            
            # Remove timestamps fora da janela de 60s
            self.timestamps = [t for t in self.timestamps if now - t < 60.0]
            
            # Se atingiu o limite, aguarda
            if len(self.timestamps) >= self.rate_limit:
                sleep_time = 60.0 / self.rate_limit
                time.sleep(sleep_time)
                now = time.time()
            
            self.timestamps.append(now)
