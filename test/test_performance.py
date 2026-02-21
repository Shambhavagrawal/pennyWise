# Test Type: Integration Test
# Validation: Server uptime, memory usage, and thread count reporting
# Command: pytest test/test_performance.py -v

import re


class TestPerformanceEndpoint:
    def test_returns_all_fields(self, client):
        resp = client.get("/blackrock/challenge/v1/performance")
        assert resp.status_code == 200
        data = resp.json()
        assert "time" in data
        assert "memory" in data
        assert "threads" in data

    def test_time_format(self, client):
        resp = client.get("/blackrock/challenge/v1/performance")
        data = resp.json()
        assert re.match(r"\d{2}:\d{2}:\d{2}\.\d{3}", data["time"])

    def test_memory_parseable(self, client):
        resp = client.get("/blackrock/challenge/v1/performance")
        data = resp.json()
        mem = float(data["memory"].replace(" MB", ""))
        assert mem > 0

    def test_threads_positive(self, client):
        resp = client.get("/blackrock/challenge/v1/performance")
        data = resp.json()
        assert isinstance(data["threads"], int)
        assert data["threads"] > 0
