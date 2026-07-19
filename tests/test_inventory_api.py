from __future__ import annotations


def test_inventory_recommendations_return_actions(api_get) -> None:
    response = api_get("/inventory/recommendations?limit=5")
    payload = response.json()

    assert response.status_code == 200
    assert payload["metadata"]["dataset"] == "inventory_recommendations"
    assert payload["metadata"]["summary"]["recommendation_count"] >= len(payload["data"])


def test_inventory_abc_and_xyz_are_available(api_get) -> None:
    abc = api_get("/inventory/abc?limit=5").json()
    xyz = api_get("/inventory/xyz?limit=5").json()

    assert abc["metadata"]["dataset"] == "abc_analysis"
    assert xyz["metadata"]["dataset"] == "xyz_analysis"
    assert isinstance(abc["data"], list)
    assert isinstance(xyz["data"], list)

