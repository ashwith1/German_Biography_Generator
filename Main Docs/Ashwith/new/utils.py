import time

class RateLimiter:
    def __init__(self, calls, period):
        self.calls = calls
        self.period = period
        self.timing = []

    def wait(self):
        current = time.time()
        if len(self.timing) >= self.calls:
            elapsed = current - self.timing[0]
            if elapsed < self.period:
                time.sleep(self.period - elapsed)
            self.timing.pop(0)
        self.timing.append(time.time())