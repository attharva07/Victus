import itertools
import threading
from datetime import datetime, timezone

_counter_lock = threading.Lock()
_counters = {}


def _next_counter(prefix: str) -> int:
    with _counter_lock:
        _counters.setdefault(prefix, itertools.count(1))
        return next(_counters[prefix])


def generate_id(prefix: str) -> str:
    now = datetime.now(timezone.utc)
    stamp = now.strftime('%Y_%m_%d')
    counter = _next_counter(prefix)
    return f"{prefix}_{stamp}_{counter:04d}"
