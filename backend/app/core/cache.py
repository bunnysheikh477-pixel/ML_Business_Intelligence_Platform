
from __future__ import annotations

import threading
import time
from typing import Any, Hashable


class TTLCache:
    """Small thread-safe in-process cache with time-based expiry.

    Used to avoid rebuilding every Plotly figure on repeated requests for the
    same dataset while the underlying file has not changed.
    """

    def __init__(self, ttl_seconds: float = 60.0, max_entries: int = 128):
        self.ttl_seconds = max(float(ttl_seconds), 0.0)
        self.max_entries = max(int(max_entries), 1)
        self._store: dict[Hashable, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: Hashable) -> Any | None:
        if self.ttl_seconds <= 0:
            return None

        with self._lock:
            entry = self._store.get(key)

            if entry is None:
                return None

            expires_at, value = entry

            if expires_at < time.monotonic():
                self._store.pop(key, None)
                return None

            return value

    def set(self, key: Hashable, value: Any) -> None:
        if self.ttl_seconds <= 0:
            return

        with self._lock:
            if len(self._store) >= self.max_entries:
                oldest = min(
                    self._store.items(),
                    key=lambda item: item[1][0],
                )
                self._store.pop(oldest[0], None)

            self._store[key] = (time.monotonic() + self.ttl_seconds, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
