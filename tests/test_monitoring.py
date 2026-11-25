
"""
Automated tests for RAG application monitoring.

Tests:
- Initial metric values
- Successful and failed HTTP requests
- Status code counters
- Retrieval and generation timings
- Average duration calculations
- Negative duration handling
- Snapshot isolation
- FastAPI /metrics endpoint

No Groq API calls are required.
"""

import pytest

from fastapi.testclient import TestClient

from app.core.monitoring import MonitoringService
from app.main import app


@pytest.fixture
def monitor():
    """Create isolated monitoring counters for each test."""
    return MonitoringService()


class TestMonitoringService:

    def test_initial_metrics(self, monitor):
        metrics = monitor.get_metrics()

        assert metrics["requests"]["total"] == 0
        assert metrics["requests"]["successful"] == 0
        assert metrics["requests"]["failed"] == 0

        assert metrics["rag_performance"]["retrieval_calls"] == 0
        assert metrics["rag_performance"]["generation_calls"] == 0

        assert metrics["uptime_seconds"] >= 0

    def test_successful_request(self, monitor):
        monitor.record_request(
            status_code=200,
            duration_ms=100.0,
        )

        metrics = monitor.get_metrics()["requests"]

        assert metrics["total"] == 1
        assert metrics["successful"] == 1
        assert metrics["failed"] == 0
        assert metrics["status_codes"]["200"] == 1
        assert metrics["average_duration_ms"] == 100.0

    def test_created_and_deleted_requests(self, monitor):
        monitor.record_request(201, 50.0)
        monitor.record_request(204, 30.0)

        metrics = monitor.get_metrics()["requests"]

        assert metrics["total"] == 2
        assert metrics["successful"] == 2
        assert metrics["failed"] == 0
        assert metrics["status_codes"]["201"] == 1
        assert metrics["status_codes"]["204"] == 1

    @pytest.mark.parametrize(
        "status_code",
        [400, 404, 409, 415, 422, 429, 500, 503],
    )
    def test_failed_request(self, monitor, status_code):
        monitor.record_request(
            status_code=status_code,
            duration_ms=20.0,
        )

        metrics = monitor.get_metrics()["requests"]

        assert metrics["total"] == 1
        assert metrics["successful"] == 0
        assert metrics["failed"] == 1
        assert metrics["status_codes"][str(status_code)] == 1

    def test_average_request_duration(self, monitor):
        monitor.record_request(200, 100.0)
        monitor.record_request(200, 200.0)
        monitor.record_request(400, 300.0)

        metrics = monitor.get_metrics()["requests"]

        assert metrics["total"] == 3
        assert metrics["successful"] == 2
        assert metrics["failed"] == 1
        assert metrics["average_duration_ms"] == 200.0

    def test_retrieval_metrics(self, monitor):
        monitor.record_retrieval(100.0)
        monitor.record_retrieval(300.0)

        metrics = monitor.get_metrics()["rag_performance"]

        assert metrics["retrieval_calls"] == 2
        assert metrics["average_retrieval_ms"] == 200.0

    def test_generation_metrics(self, monitor):
        monitor.record_generation(500.0)
        monitor.record_generation(1000.0)

        metrics = monitor.get_metrics()["rag_performance"]

        assert metrics["generation_calls"] == 2
        assert metrics["average_generation_ms"] == 750.0

    def test_retrieval_and_generation_are_independent(
        self,
        monitor,
    ):
        monitor.record_retrieval(125.0)

        metrics = monitor.get_metrics()["rag_performance"]

        assert metrics["retrieval_calls"] == 1
        assert metrics["generation_calls"] == 0

        monitor.record_generation(650.0)

        metrics = monitor.get_metrics()["rag_performance"]

        assert metrics["retrieval_calls"] == 1
        assert metrics["generation_calls"] == 1

    def test_negative_durations_are_clamped(self, monitor):
        monitor.record_request(200, -50.0)
        monitor.record_retrieval(-100.0)
        monitor.record_generation(-200.0)

        metrics = monitor.get_metrics()

        assert metrics["requests"]["average_duration_ms"] == 0.0
        assert (
            metrics["rag_performance"]["average_retrieval_ms"]
            == 0.0
        )
        assert (
            metrics["rag_performance"]["average_generation_ms"]
            == 0.0
        )

    def test_snapshot_does_not_modify_internal_counters(
        self,
        monitor,
    ):
        monitor.record_request(200, 25.0)

        snapshot = monitor.get_metrics()
        snapshot["requests"]["status_codes"]["200"] = 999

        new_snapshot = monitor.get_metrics()

        assert new_snapshot["requests"]["status_codes"]["200"] == 1


class TestMonitoringAPI:

    def test_metrics_endpoint(self):
        """Check that FastAPI exposes monitoring fields."""
        with TestClient(app) as client:
            response = client.get("/metrics")

        assert response.status_code == 200

        data = response.json()

        assert "uptime_seconds" in data
        assert "requests" in data
        assert "rag_performance" in data

        assert "total" in data["requests"]
        assert "successful" in data["requests"]
        assert "failed" in data["requests"]
        assert "average_duration_ms" in data["requests"]

        assert "retrieval_calls" in data["rag_performance"]
        assert "generation_calls" in data["rag_performance"]
        assert "average_retrieval_ms" in data["rag_performance"]
        assert "average_generation_ms" in data["rag_performance"]

    def test_health_endpoint_still_works(self):
        """Monitoring must not break existing health checks."""
        with TestClient(app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
