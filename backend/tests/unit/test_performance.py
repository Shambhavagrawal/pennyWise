import re

import pytest

from src.services.performance_service import format_uptime


class TestFormatUptime:
    def test_zero_seconds(self):
        assert format_uptime(0) == "00:00:00.000"

    def test_minutes_and_seconds(self):
        assert format_uptime(714.135) == "00:11:54.135"

    def test_hours(self):
        assert format_uptime(3661.5) == "01:01:01.500"

    def test_fractional_milliseconds(self):
        result = format_uptime(1.9999)
        assert result == "00:00:01.999"

    def test_large_uptime(self):
        result = format_uptime(86400)  # 24 hours
        assert result == "24:00:00.000"

    def test_sub_second(self):
        result = format_uptime(0.456)
        assert result == "00:00:00.456"


class TestPerformanceEndpoint:
    @pytest.mark.api
    async def test_returns_all_fields(self, client):
        response = await client.get("/blackrock/challenge/v1/performance")
        assert response.status_code == 200
        data = response.json()
        assert "time" in data
        assert "memory" in data
        assert "threads" in data

    @pytest.mark.api
    async def test_time_format(self, client):
        response = await client.get("/blackrock/challenge/v1/performance")
        data = response.json()
        assert re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}$", data["time"])

    @pytest.mark.api
    async def test_memory_is_parseable_float(self, client):
        response = await client.get("/blackrock/challenge/v1/performance")
        data = response.json()
        assert isinstance(data["memory"], str)
        mem_value = float(data["memory"])
        assert mem_value > 0

    @pytest.mark.api
    async def test_threads_is_positive_integer(self, client):
        response = await client.get("/blackrock/challenge/v1/performance")
        data = response.json()
        assert isinstance(data["threads"], int)
        assert data["threads"] > 0
