from collections import deque
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)

class SignalEngine:
    def __init__(self):
        # Dictionary of deques: ticker -> deque of (timestamp, score, weight)
        self.history = {}
        self.window_minutes = 15
        self.lock = threading.Lock()

    def _cleanup(self, ticker):
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.window_minutes)
        while self.history[ticker] and self.history[ticker][0][0] < cutoff:
            self.history[ticker].popleft()

    def add_score(self, ticker, score, source_weight=1.0):
        ticker = ticker.upper()
        with self.lock:
            if ticker not in self.history:
                self.history[ticker] = deque()
            
            self.history[ticker].append((datetime.utcnow(), score, source_weight))
            self._cleanup(ticker)

    def get_signal(self, ticker) -> str:
        ticker = ticker.upper()
        with self.lock:
            if ticker not in self.history or not self.history[ticker]:
                return "HOLD"
            
            self._cleanup(ticker)
            
            if not self.history[ticker]:
                return "HOLD"

            total_weighted_score = sum(score * weight for _, score, weight in self.history[ticker])
            total_weight = sum(weight for _, _, weight in self.history[ticker])
            
            if total_weight == 0:
                return "HOLD"
                
            avg_score = total_weighted_score / total_weight
            
            logger.info(f"SignalEngine [{ticker}]: Computed weighted avg_score = {avg_score:.3f} (total_weight={total_weight:.1f})")
            
            if avg_score > 0.25:
                return "BUY"
            elif avg_score < -0.25:
                return "SELL"
            else:
                return "HOLD"
