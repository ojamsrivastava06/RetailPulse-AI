from __future__ import annotations


def test_customer_segments_and_rfm_are_available(api_get) -> None:
    segments = api_get("/customer/segments?limit=3").json()
    rfm = api_get("/customer/rfm?limit=3").json()

    assert segments["metadata"]["dataset"] == "customer_segments"
    assert rfm["metadata"]["dataset"] == "rfm_table"
    assert segments["metadata"]["summary"]["customers"] >= len(segments["data"])


def test_customer_clv_and_health_return_summaries(api_get) -> None:
    clv = api_get("/customer/clv?limit=3").json()
    health = api_get("/customer/health?limit=3").json()

    assert "average_clv" in clv["metadata"]["summary"]
    assert "average_health_score" in health["metadata"]["summary"]

