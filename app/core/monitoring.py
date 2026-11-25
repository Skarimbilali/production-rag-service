
"""
In-memory monitoring for the Production RAG Service.

Tracks:
- HTTP request counts and latency
- Error counts by HTTP status
- Retrieval and generation duration

Does not store questions, documents, or API credentials.

Metrics reset when the application process restarts.
Each worker maintains independent metrics.
"""

import threading
import time

from collections import defaultdict
from statistics import mean


class MonitoringService:
    """Thread-safe in-memory performance counters."""

    def __init__(self):
        self._lock = threading.Lock()
        self._started_at = time.time()

        self._request_count = 0
        self._success_count = 0
        self._error_count = 0

        self._http_status_counts = defaultdict(int)

        self._request_durations_ms = []
        self._retrieval_durations_ms = []
        self._generation_durations_ms = []

    @staticmethod
    def _average(values):
        """Return zero for an empty measurement set."""
        return round(mean(values), 2) if values else 0.0

    def record_request(
        self,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Record completed HTTP request measurements."""
        with self._lock:
            self._request_count += 1

            self._http_status_counts[str(status_code)] += 1

            if 200 <= status_code < 400:
                self._success_count += 1
            else:
                self._error_count += 1

            self._request_durations_ms.append(
                max(0.0, duration_ms)
            )

    def record_retrieval(self, duration_ms: float) -> None:
        """Record document retrieval duration."""
        with self._lock:
            self._retrieval_durations_ms.append(
                max(0.0, duration_ms)
            )

    def record_generation(self, duration_ms: float) -> None:
        """Record Groq generation duration."""
        with self._lock:
            self._generation_durations_ms.append(
                max(0.0, duration_ms)
            )

    def get_metrics(self) -> dict:
        """Return a thread-safe snapshot of current metrics."""
        with self._lock:
            return {
                "uptime_seconds": round(
                    time.time() - self._started_at,
                    2,
                ),
                "requests": {
                    "total": self._request_count,
                    "successful": self._success_count,
                    "failed": self._error_count,
                    "status_codes": dict(
                        self._http_status_counts
                    ),
                    "average_duration_ms": self._average(
                        self._request_durations_ms
                    ),
                },
                "rag_performance": {
                    "retrieval_calls": len(
                        self._retrieval_durations_ms
                    ),
                    "average_retrieval_ms": self._average(
                        self._retrieval_durations_ms
                    ),
                    "generation_calls": len(
                        self._generation_durations_ms
                    ),
                    "average_generation_ms": self._average(
                        self._generation_durations_ms
                    ),
                },
            }


# Shared monitoring instance for the application process.
monitoring_service = MonitoringService()
