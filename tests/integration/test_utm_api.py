"""
Integration tests for UTM Tracking API
"""
import pytest


class TestUTMAPI:
    """Test /api/v1/utm endpoints"""

    def test_generate_utm_link(self, client, auth_headers):
        """Test UTM link generation"""
        response = client.post(
            "/api/v1/utm/generate",
            headers=auth_headers,
            json={
                "base_url": "https://t.me/testbot",
                "source": "tiktok",
                "campaign": "test_campaign_jan_2026",
                "link_type": "direct"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "utm_id" in data
        assert "landing_url" in data or "direct_url" in data
        assert data["utm_source"] == "tiktok"

    def test_track_click(self, client, auth_headers):
        """Test click tracking"""
        # First create a UTM link
        create_response = client.post(
            "/api/v1/utm/generate",
            headers=auth_headers,
            json={
                "base_url": "https://t.me/testbot",
                "source": "instagram",
                "campaign": "test_campaign",
                "link_type": "landing"
            }
        )
        utm_id = create_response.json()["utm_id"]

        # Track a click
        track_response = client.get(
            f"/api/v1/utm/track/{utm_id}",
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)"}
        )

        # Should redirect or return tracking confirmation
        assert track_response.status_code in [200, 302, 307]

    def test_track_conversion(self, client):
        """Test conversion webhook (no auth required)"""
        # Create a traffic source first
        from database.models import TrafficSource, User

        # This test needs proper setup with test_db
        # Simplified version:
        response = client.post(
            "/api/v1/utm/webhook/conversion",
            json={
                "utm_id": "test_utm_123",
                "customer_id": "telegram_12345",
                "amount": 1000,  # $10.00
                "currency": "USD",
                "product_name": "Test Product"
            }
        )

        # Should accept webhook even if UTM doesn't exist (idempotent)
        assert response.status_code in [200, 201, 404]

    def test_get_analytics(self, client, auth_headers):
        """Test analytics endpoint"""
        response = client.get(
            "/api/v1/utm/sources",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "sources" in data

    def test_get_traffic_sources(self, client, auth_headers):
        """Test get all traffic sources"""
        response = client.get(
            "/api/v1/utm/traffic-sources",
            headers=auth_headers,
            params={"limit": 10, "offset": 0}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
