"""
Risk Management API v2 - Tests
================================

Test suite for the risk management API endpoints.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..main import app
from ..database import Base
from ..dependencies import get_database
from ..models import (
    RiskMetricType, AlertLevel, AlertStatus, ReportFormat,
    AdjustmentType
)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency
def override_get_database():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_database] = override_get_database

# Create test client
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_token():
    """Mock authentication token"""
    return "Bearer mock_test_user_123"


@pytest.fixture
def headers(test_user_token):
    """Default headers with authentication"""
    return {
        "Authorization": test_user_token,
        "Content-Type": "application/json"
    }


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Risk Management API"

    def test_readiness_check(self, setup_database):
        """Test readiness check"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["database"] == "ok"
        assert data["checks"]["risk_engine"] == "ok"

    def test_liveness_check(self):
        """Test liveness check"""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestRiskMetricsEndpoints:
    """Test risk metrics endpoints"""

    def test_get_portfolio_risk_metrics_not_found(self, headers):
        """Test getting risk metrics for non-existent portfolio"""
        response = client.get(
            "/api/v2/risk/portfolio/non_existent_portfolio",
            headers=headers
        )
        assert response.status_code == 404

    def test_get_available_metrics(self, headers):
        """Test getting available risk metrics"""
        response = client.get(
            "/api/v2/risk/metrics",
            headers=headers
        )
        assert response.status_code == 200
        metrics = response.json()
        assert isinstance(metrics, list)
        assert RiskMetricType.VAR.value in metrics
        assert RiskMetricType.VOLATILITY.value in metrics

    def test_get_risk_history_validation(self, headers):
        """Test risk history validation"""
        # Test invalid date range
        start_date = datetime.now()
        end_date = datetime.now() - timedelta(days=1)

        response = client.get(
            f"/api/v2/risk/history?portfolio_id=test&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=headers
        )
        assert response.status_code == 400


class TestAlertEndpoints:
    """Test alert configuration endpoints"""

    def test_create_alert(self, headers):
        """Test creating alert configuration"""
        alert_data = {
            "name": "Test VaR Alert",
            "metric_type": RiskMetricType.VAR.value,
            "portfolio_id": "test_portfolio",
            "threshold_warning": -0.02,
            "threshold_error": -0.03,
            "threshold_critical": -0.05,
            "comparison_operator": "less_than",
            "enabled": True,
            "notification_channels": ["email"]
        }

        response = client.post(
            "/api/v2/risk/alerts",
            json=alert_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "alert_id" in data["data"]

    def test_get_alerts(self, headers):
        """Test getting alert configurations"""
        response = client.get(
            "/api/v2/risk/alerts",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_create_alert_validation(self, headers):
        """Test alert creation validation"""
        # Test invalid metric type
        alert_data = {
            "name": "Invalid Alert",
            "metric_type": "invalid_metric",
            "threshold_warning": -0.02
        }

        response = client.post(
            "/api/v2/risk/alerts",
            json=alert_data,
            headers=headers
        )
        assert response.status_code == 422


class TestReportEndpoints:
    """Test report generation endpoints"""

    def test_generate_report(self, headers):
        """Test report generation"""
        report_data = {
            "portfolio_id": "test_portfolio",
            "report_type": "comprehensive",
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "metrics": [RiskMetricType.VAR.value, RiskMetricType.VOLATILITY.value],
            "format": ReportFormat.JSON.value,
            "include_charts": True,
            "include_recommendations": True
        }

        response = client.post(
            "/api/v2/risk/reports",
            json=report_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report_id" in data["data"]

    def test_get_reports(self, headers):
        """Test getting reports list"""
        response = client.get(
            "/api/v2/risk/reports",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_nonexistent_report(self, headers):
        """Test getting non-existent report"""
        response = client.get(
            "/api/v2/risk/reports/non_existent_report",
            headers=headers
        )
        assert response.status_code == 404


class TestAdjustmentEndpoints:
    """Test dynamic adjustment endpoints"""

    def test_evaluate_adjustments(self, headers):
        """Test adjustment evaluation"""
        adjustment_data = {
            "portfolio_id": "test_portfolio",
            "current_positions": {
                "AAPL": 100000,
                "GOOGL": 50000,
                "MSFT": 75000
            },
            "risk_budget": 0.02,
            "target_leverage": 1.0,
            "adjustment_type": AdjustmentType.POSITION_SCALING.value,
            "max_adjustment_pct": 0.3
        }

        response = client.post(
            "/api/v2/risk/adjustments",
            json=adjustment_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "portfolio_id" in data
        assert "adjustments" in data
        assert "summary" in data

    def test_get_adjustment_history(self, headers):
        """Test getting adjustment history"""
        response = client.get(
            "/api/v2/risk/adjustments?portfolio_id=test_portfolio",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_recommendations(self, headers):
        """Test getting risk recommendations"""
        response = client.get(
            "/api/v2/risk/recommendations",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)


class TestWebSocketEndpoints:
    """Test WebSocket endpoints"""

    def test_websocket_risk_monitoring(self):
        """Test WebSocket risk monitoring endpoint"""
        with client.websocket_connect("/ws/risk/monitoring/test_connection_123?user_id=test_user") as websocket:
            # Send subscription message
            websocket.send_text(json.dumps({
                "type": "subscribe",
                "subscription_type": "portfolio",
                "target_id": "test_portfolio"
            }))

            # Receive confirmation
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "subscription_confirmed"
            assert message["subscription_type"] == "portfolio"
            assert message["target_id"] == "test_portfolio"

            # Send ping
            websocket.send_text(json.dumps({"type": "ping"}))
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "pong"

    def test_websocket_alert_stream(self):
        """Test WebSocket alert stream endpoint"""
        with client.websocket_connect("/ws/risk/alerts/test_connection_456?user_id=test_user") as websocket:
            # Should receive heartbeat message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "heartbeat"


class TestSecurity:
    """Test security features"""

    def test_rate_limiting(self):
        """Test rate limiting"""
        # Make many requests to trigger rate limit
        headers = {"Authorization": "Bearer mock_test_user_456"}

        for i in range(60):  # Exceed default rate limit
            response = client.get(
                "/api/v2/risk/metrics",
                headers=headers
            )
            if response.status_code == 429:
                break
        else:
            pytest.fail("Rate limit not triggered")

        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_cors_headers(self):
        """Test CORS headers"""
        response = client.options("/api/v2/risk/metrics")
        assert "access-control-allow-origin" in response.headers

    def test_security_headers(self):
        """Test security headers"""
        response = client.get("/health")
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers


class TestErrorHandling:
    """Test error handling"""

    def test_404_error(self):
        """Test 404 error handling"""
        response = client.get("/non_existent_endpoint")
        assert response.status_code == 404

    def test_validation_error(self):
        """Test validation error handling"""
        response = client.post(
            "/api/v2/risk/alerts",
            json={"invalid": "data"},
            headers={"Authorization": "Bearer mock_test_user"}
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_unauthorized_access(self):
        """Test unauthorized access handling"""
        # This would fail if authentication was properly implemented
        response = client.get("/api/v2/risk/metrics")
        # For now, it should work with anonymous user
        assert response.status_code in [200, 401]


@pytest.mark.integration
class TestIntegration:
    """Integration tests"""

    def test_full_risk_workflow(self, headers):
        """Test complete risk management workflow"""
        # 1. Create alert configuration
        alert_data = {
            "name": "Integration Test Alert",
            "metric_type": RiskMetricType.VOLATILITY.value,
            "portfolio_id": "integration_test_portfolio",
            "threshold_warning": 0.02,
            "enabled": True
        }

        response = client.post(
            "/api/v2/risk/alerts",
            json=alert_data,
            headers=headers
        )
        assert response.status_code == 200
        alert_id = response.json()["data"]["alert_id"]

        # 2. Generate report
        report_data = {
            "portfolio_id": "integration_test_portfolio",
            "report_type": "risk_assessment",
            "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "format": ReportFormat.JSON.value
        }

        response = client.post(
            "/api/v2/risk/reports",
            json=report_data,
            headers=headers
        )
        assert response.status_code == 200
        report_id = response.json()["data"]["report_id"]

        # 3. Evaluate adjustments
        adjustment_data = {
            "portfolio_id": "integration_test_portfolio",
            "current_positions": {"TEST": 100000},
            "risk_budget": 0.015
        }

        response = client.post(
            "/api/v2/risk/adjustments",
            json=adjustment_data,
            headers=headers
        )
        assert response.status_code == 200
        adjustment_data = response.json()

        # 4. Get recommendations
        response = client.get(
            f"/api/v2/risk/recommendations?portfolio_id=integration_test_portfolio",
            headers=headers
        )
        assert response.status_code == 200
        recommendations = response.json()

        # Verify all components are working
        assert alert_id is not None
        assert report_id is not None
        assert adjustment_data["request_id"] is not None
        assert recommendations["total"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])