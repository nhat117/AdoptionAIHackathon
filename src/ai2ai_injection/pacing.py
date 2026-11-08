"""Per-process shared pacing and explicit Retry-After handling."""

import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


class RequestPacer:
    def __init__(self, interval=2.0, clock=time.monotonic, sleep=time.sleep):
        self.interval = interval
        self.clock = clock
        self.sleep = sleep
        self.next_at = 0.0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            delay = max(0.0, self.next_at - self.clock())
            if delay:
                self.sleep(delay)
            self.next_at = self.clock() + self.interval

    def defer(self, seconds):
        with self.lock:
            self.next_at = max(self.next_at, self.clock() + seconds)


def retry_after_seconds(value, fallback=60.0):
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            return max(0.0, (date - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return fallback


SHARED_PACER = RequestPacer()
