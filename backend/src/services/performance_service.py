import os
import threading
import time

import psutil

from src.models.challenge import PerformanceOutput


def format_uptime(elapsed_seconds: float) -> str:
    total_ms = int(elapsed_seconds * 1000)
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


def get_performance_metrics(start_time: float) -> PerformanceOutput:
    elapsed = time.time() - start_time
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / (1024 * 1024)

    return PerformanceOutput(
        time=format_uptime(elapsed),
        memory=f"{memory_mb:.2f}",
        threads=threading.active_count(),
    )
