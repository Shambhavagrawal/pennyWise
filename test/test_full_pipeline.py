# Test Type: Integration Test
# Validation: Full processing pipeline with spec worked example data
# Command: pytest test/test_full_pipeline.py -v

SPEC_TRANSACTIONS = [
    {"date": "2023-10-12 14:23:00", "amount": 250},
    {"date": "2023-02-28 09:15:00", "amount": 375},
    {"date": "2023-07-01 12:00:00", "amount": 620},
    {"date": "2023-12-17 18:30:00", "amount": 480},
]

SPEC_PAYLOAD = {
    "age": 29,
    "wage": 50000,
    "inflation": 5.5,
    "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
    "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
    "k": [
        {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59"},
        {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
    ],
    "transactions": SPEC_TRANSACTIONS,
}


class TestParseStep:
    def test_ceiling_remanent_for_each(self, client):
        resp = client.post("/blackrock/challenge/v1/transactions:parse", json=SPEC_TRANSACTIONS)
        data = resp.json()
        expected = [
            {"date": "2023-10-12 14:23:00", "amount": 250.0, "ceiling": 300.0, "remanent": 50.0},
            {"date": "2023-02-28 09:15:00", "amount": 375.0, "ceiling": 400.0, "remanent": 25.0},
            {"date": "2023-07-01 12:00:00", "amount": 620.0, "ceiling": 700.0, "remanent": 80.0},
            {"date": "2023-12-17 18:30:00", "amount": 480.0, "ceiling": 500.0, "remanent": 20.0},
        ]
        assert data == expected


class TestFilterStep:
    def test_zero_remanent_omitted(self, client):
        resp = client.post(
            "/blackrock/challenge/v1/transactions:filter",
            json={**SPEC_PAYLOAD, "age": 29},  # age not used by filter but included for clarity
        )
        data = resp.json()
        # July (620) has q override to 0, so omitted from valid
        valid_dates = [v["date"] for v in data["valid"]]
        assert "2023-07-01 12:00:00" not in valid_dates
        assert len(data["valid"]) == 3

    def test_adjusted_remanents(self, client):
        resp = client.post("/blackrock/challenge/v1/transactions:filter", json=SPEC_PAYLOAD)
        data = resp.json()
        remanents = {v["date"]: v["remanent"] for v in data["valid"]}
        # Oct: 50 + 25(p) = 75, Feb: 25, Dec: 20 + 25(p) = 45
        assert remanents["2023-10-12 14:23:00"] == 75
        assert remanents["2023-02-28 09:15:00"] == 25
        assert remanents["2023-12-17 18:30:00"] == 45


class TestNpsReturnsStep:
    def test_pinned_profit_k1(self, client):
        resp = client.post("/blackrock/challenge/v1/returns:nps", json=SPEC_PAYLOAD)
        data = resp.json()
        k1 = data["savingsByDates"][1]
        assert k1["amount"] == 145.0
        assert k1["profit"] == 86.88
        assert k1["taxBenefit"] == 0.0

    def test_totals(self, client):
        resp = client.post("/blackrock/challenge/v1/returns:nps", json=SPEC_PAYLOAD)
        data = resp.json()
        # Includes all 4 valid transactions (even July before zero-remanent removal)
        assert data["totalTransactionAmount"] == 1725.0
        assert data["totalCeiling"] == 1900.0


class TestIndexReturnsStep:
    def test_profit_differs_from_nps(self, client):
        nps = client.post("/blackrock/challenge/v1/returns:nps", json=SPEC_PAYLOAD).json()
        idx = client.post("/blackrock/challenge/v1/returns:index", json=SPEC_PAYLOAD).json()
        # Index profit should be higher due to 14.49% vs 7.11%
        assert idx["savingsByDates"][1]["profit"] > nps["savingsByDates"][1]["profit"]
        # But totals are identical (same pipeline)
        assert idx["totalTransactionAmount"] == nps["totalTransactionAmount"]


class TestFieldNames:
    def test_nps_field_names(self, client):
        resp = client.post("/blackrock/challenge/v1/returns:nps", json=SPEC_PAYLOAD)
        data = resp.json()
        assert "totalTransactionAmount" in data
        assert "totalCeiling" in data
        assert "savingsByDates" in data
        s = data["savingsByDates"][0]
        assert "profit" in s
        assert "taxBenefit" in s

    def test_index_field_names(self, client):
        resp = client.post("/blackrock/challenge/v1/returns:index", json=SPEC_PAYLOAD)
        data = resp.json()
        assert "totalTransactionAmount" in data
        assert "totalCeiling" in data
        assert "savingsByDates" in data
