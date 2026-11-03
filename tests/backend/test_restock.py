"""
Tests for restocking API endpoints.
"""
import pytest


TREND_RANK = {"increasing": 0, "stable": 1, "decreasing": 2}


class TestRestockRecommendations:
    """Test suite for GET /api/restock/recommendations."""

    def test_zero_budget_recommends_nothing(self, client):
        """Test that a zero budget yields no items."""
        response = client.get("/api/restock/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget fails validation."""
        response = client.get("/api/restock/recommendations?budget=-1")
        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.parametrize("budget", ["nan", "inf", "-inf"])
    def test_non_finite_budget_rejected(self, client, budget):
        """Test that NaN/Infinity budgets are rejected instead of causing a 500."""
        response = client.get(f"/api/restock/recommendations?budget={budget}")
        assert response.status_code == 422

    def test_missing_budget_rejected(self, client):
        """Test that budget is required."""
        response = client.get("/api/restock/recommendations")
        assert response.status_code == 422

    def test_recommendation_structure(self, client):
        """Test that each recommended line has the expected fields and types."""
        data = client.get("/api/restock/recommendations?budget=20000").json()
        assert len(data["items"]) > 0

        for line in data["items"]:
            for field in ["sku", "name", "category", "trend", "on_hand", "forecasted_demand",
                          "shortfall", "quantity", "unit_cost", "line_total", "lead_time_days"]:
                assert field in line
            assert isinstance(line["quantity"], int)
            assert line["quantity"] > 0
            assert line["quantity"] <= line["shortfall"]

    def test_total_never_exceeds_budget(self, client):
        """Test that the recommended total stays within the budget for several budgets."""
        for budget in [100, 1000, 7500, 20000, 60000, 1000000]:
            data = client.get(f"/api/restock/recommendations?budget={budget}").json()
            assert data["total_cost"] <= budget
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_line_totals_match_quantity_times_cost(self, client):
        """Test that line totals and the order total are consistent."""
        data = client.get("/api/restock/recommendations?budget=20000").json()

        for line in data["items"]:
            assert abs(line["line_total"] - line["quantity"] * line["unit_cost"]) < 0.01
        assert abs(data["total_cost"] - sum(l["line_total"] for l in data["items"])) < 0.01

    def test_items_ranked_by_trend_then_shortfall(self, client):
        """Test that growing demand comes first, then the larger shortfall."""
        # Large budget so ranking, not budget exhaustion, determines the order
        items = client.get("/api/restock/recommendations?budget=1000000").json()["items"]

        keys = [(TREND_RANK[i["trend"]], -i["shortfall"]) for i in items]
        assert keys == sorted(keys)

    def test_item_with_surplus_stock_not_recommended(self, client):
        """Test that SKUs whose on-hand stock covers forecasted demand are skipped."""
        # PSU-501: 420 on hand vs 252 forecasted
        items = client.get("/api/restock/recommendations?budget=1000000").json()["items"]
        assert "PSU-501" not in [i["sku"] for i in items]

    def test_unstocked_sku_shortfall_equals_forecast(self, client):
        """Test that a SKU missing from inventory counts as zero on hand."""
        items = client.get("/api/restock/recommendations?budget=1000000").json()["items"]
        widget = next(i for i in items if i["sku"] == "WDG-001")

        assert widget["on_hand"] == 0
        assert widget["shortfall"] == widget["forecasted_demand"]
        assert widget["quantity"] == widget["shortfall"]

    def test_small_budget_partially_fills_top_priority(self, client):
        """Test that a tight budget buys a partial quantity instead of nothing."""
        data = client.get("/api/restock/recommendations?budget=100").json()
        assert len(data["items"]) > 0
        assert data["items"][0]["quantity"] < data["items"][0]["shortfall"]


class TestRestockOrders:
    """Test suite for POST and GET /api/restock-orders."""

    def _order_payload(self, client, budget=20000):
        """Build a valid order from the current recommendations."""
        recs = client.get(f"/api/restock/recommendations?budget={budget}").json()
        return {
            "budget": budget,
            "items": [{"sku": i["sku"], "quantity": i["quantity"]} for i in recs["items"]],
        }, recs

    def test_place_order_success(self, client):
        """Test submitting a recommended order."""
        payload, recs = self._order_payload(client)
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert len(order["items"]) == len(payload["items"])
        assert abs(order["total_value"] - recs["total_cost"]) < 0.01

    def test_lead_time_is_longest_item(self, client):
        """Test that order lead time is the max over its items and sets the delivery date."""
        payload, _ = self._order_payload(client)
        order = client.post("/api/restock-orders", json=payload).json()

        assert order["lead_time_days"] == max(i["lead_time_days"] for i in order["items"])
        order_date = order["order_date"][:10]
        delivery = order["expected_delivery"][:10]
        assert delivery > order_date

    def test_server_recomputes_prices(self, client):
        """Test that client-supplied prices are ignored and the catalog cost is used."""
        payload = {"budget": 1000, "items": [{"sku": "WDG-001", "quantity": 10, "unit_cost": 0.01}]}
        order = client.post("/api/restock-orders", json=payload).json()

        assert order["items"][0]["unit_cost"] == 15.0
        assert order["total_value"] == 150.0

    def test_submitted_order_listed(self, client):
        """Test that a placed order appears in GET /api/restock-orders, newest first."""
        payload, _ = self._order_payload(client)
        first = client.post("/api/restock-orders", json=payload).json()
        second = client.post("/api/restock-orders", json=payload).json()

        listed = client.get("/api/restock-orders").json()
        ids = [o["id"] for o in listed]
        assert first["id"] in ids and second["id"] in ids
        # Newest first
        assert ids.index(second["id"]) < ids.index(first["id"])

    def test_empty_order_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_non_positive_quantity_rejected(self, client, quantity):
        """Test that zero or negative quantities are rejected."""
        payload = {"budget": 1000, "items": [{"sku": "WDG-001", "quantity": quantity}]}
        assert client.post("/api/restock-orders", json=payload).status_code == 400

    def test_unknown_sku_rejected(self, client):
        """Test that SKUs outside the forecast and catalog are rejected."""
        payload = {"budget": 1000, "items": [{"sku": "NOPE-000", "quantity": 1}]}
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400
        assert "unknown" in response.json()["detail"].lower()

    def test_duplicate_sku_rejected(self, client):
        """Test that the same SKU cannot appear twice in one order."""
        payload = {"budget": 10000, "items": [{"sku": "WDG-001", "quantity": 1},
                                              {"sku": "WDG-001", "quantity": 2}]}
        assert client.post("/api/restock-orders", json=payload).status_code == 400

    def test_over_budget_order_rejected(self, client):
        """Test that an order whose total exceeds the budget is rejected."""
        # 100 widgets at 15.00 = 1500 > 1000
        payload = {"budget": 1000, "items": [{"sku": "WDG-001", "quantity": 100}]}
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_negative_budget_rejected(self, client):
        """Test that a negative budget is rejected on submit."""
        payload = {"budget": -1, "items": [{"sku": "WDG-001", "quantity": 1}]}
        assert client.post("/api/restock-orders", json=payload).status_code == 400

    @pytest.mark.parametrize("budget", ["NaN", "Infinity"])
    def test_non_finite_budget_rejected_on_submit(self, client, budget):
        """Test that a NaN/Infinity budget cannot bypass the over-budget check."""
        # Raw JSON because Python's json encoder would also emit these tokens; be explicit
        body = '{"budget": %s, "items": [{"sku": "MTR-304", "quantity": 100000}]}' % budget
        response = client.post("/api/restock-orders", content=body,
                               headers={"Content-Type": "application/json"})
        assert response.status_code == 400

    def test_malformed_body_rejected(self, client):
        """Test that a body missing required fields fails validation."""
        assert client.post("/api/restock-orders", json={"items": []}).status_code == 422
