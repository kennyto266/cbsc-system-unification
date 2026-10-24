"""
Locust Load Testing Configuration
Simulates user behavior for load testing the CBSC system
"""

from locust import HttpUser, task, between, events
import random
import json
from datetime import datetime, timedelta

# Test data
STRATEGY_NAMES = [
    "Moving Average Strategy",
    "RSI Strategy",
    "Bollinger Bands Strategy",
    "MACD Strategy",
    "Stochastic Strategy"
]

SYMBOLS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "XRP/USDT"]

class CBSCUser(HttpUser):
    """Simulated CBSC system user"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when a user starts"""
        # Login
        self.login()

    def login(self):
        """User login"""
        login_data = {
            "username": f"user_{random.randint(1, 1000)}",
            "password": "test_password"
        }

        response = self.client.post("/api/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get("data", {}).get("access_token")
            if token:
                self.client.headers.update({
                    "Authorization": f"Bearer {token}"
                })

    @task(3)
    def view_strategies(self):
        """View strategies list"""
        self.client.get("/api/strategies")

    @task(2)
    def view_strategy_performance(self):
        """View strategy performance"""
        strategy_id = random.randint(1, 10)
        self.client.get(f"/api/strategies/{strategy_id}/performance")

    @task(2)
    def view_market_data(self):
        """View market data"""
        symbol = random.choice(SYMBOLS)
        self.client.get(f"/api/market/data/{symbol}")

    @task(1)
    def create_strategy(self):
        """Create new strategy"""
        strategy_data = {
            "name": f"Test Strategy {random.randint(1000, 9999)}",
            "description": "Created during load testing",
            "parameters": {
                "short_period": random.randint(5, 20),
                "long_period": random.randint(20, 50),
                "symbol": random.choice(SYMBOLS)
            },
            "status": "draft"
        }

        self.client.post("/api/strategies", json=strategy_data)

    @task(1)
    def update_strategy(self):
        """Update existing strategy"""
        strategy_id = random.randint(1, 10)
        update_data = {
            "name": f"Updated Strategy {random.randint(1000, 9999)}",
            "description": "Updated during load testing",
            "parameters": {
                "updated_param": f"value_{random.randint(1, 100)}"
            }
        }

        self.client.put(f"/api/strategies/{strategy_id}", json=update_data)

    @task(1)
    def get_dashboard_data(self):
        """Get dashboard data"""
        self.client.get("/api/dashboard/data")

    @task(1)
    def search_strategies(self):
        """Search strategies"""
        search_term = random.choice(["MA", "RSI", "BTC", "ETH", "active"])
        self.client.get(f"/api/strategies?search={search_term}")


class AdminUser(HttpUser):
    """Simulated admin user with higher privileges"""

    wait_time = between(2, 5)
    weight = 1  # Fewer admin users than regular users

    def on_start(self):
        """Admin login"""
        admin_data = {
            "username": "admin_user",
            "password": "admin_password"
        }

        response = self.client.post("/api/auth/login", json=admin_data)
        if response.status_code == 200:
            token = response.json().get("data", {}).get("access_token")
            if token:
                self.client.headers.update({
                    "Authorization": f"Bearer {token}",
                    "X-Admin-Role": "true"
                })

    @task(3)
    def view_all_strategies(self):
        """View all strategies (admin view)"""
        self.client.get("/api/admin/strategies")

    @task(2)
    def view_system_metrics(self):
        """View system metrics"""
        self.client.get("/api/admin/system/metrics")

    @task(2)
    def view_user_activity(self):
        """View user activity logs"""
        self.client.get("/api/admin/users/activity")

    @task(1)
    def export_strategy_data(self):
        """Export strategy performance data"""
        self.client.get("/api/admin/strategies/export")


# Event handlers for collecting statistics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log request statistics"""
    if exception:
        print(f"Request failed: {name} - {exception}")
    else:
        # Can log to external monitoring system here
        pass


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print(f"Load test starting at {datetime.now()}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print(f"Load test completed at {datetime.now()}")

    # Print summary statistics
    stats = environment.stats

    print("\n=== Load Test Summary ===")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Success rate: {(1 - stats.total.num_failures/stats.total.num_requests)*100:.2f}%")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"Requests per second: {stats.total.current_rps:.2f}")


# Custom statistics for reporting
def get_detailed_stats(environment):
    """Generate detailed statistics report"""
    stats = environment.stats

    report = {
        "test_summary": {
            "total_requests": stats.total.num_requests,
            "failed_requests": stats.total.num_failures,
            "success_rate": (1 - stats.total.num_failures/stats.total.num_requests)*100,
            "avg_response_time": stats.total.avg_response_time,
            "median_response_time": stats.total.median_response_time,
            "p95_response_time": stats.total.get_response_time_percentile(0.95),
            "p99_response_time": stats.total.get_response_time_percentile(0.99),
            "max_response_time": stats.total.max_response_time,
            "min_response_time": stats.total.min_response_time,
            "requests_per_second": stats.total.current_rps
        },
        "endpoint_stats": {}
    }

    # Per-endpoint statistics
    for name, endpoint_stats in stats.entries.items():
        if name not in ["Total", "Aggregated"]:
            report["endpoint_stats"][name] = {
                "num_requests": endpoint_stats.num_requests,
                "num_failures": endpoint_stats.num_failures,
                "avg_response_time": endpoint_stats.avg_response_time,
                "median_response_time": endpoint_stats.median_response_time,
                "p95_response_time": endpoint_stats.get_response_time_percentile(0.95),
                "requests_per_second": endpoint_stats.current_rps
            }

    return report


# Export for use in test runner
if __name__ == "__main__":
    from locust import run_single_user

    # Run a single user test for debugging
    class TestUser(CBSCUser):
        wait_time = between(0.1, 0.2)  # Faster for testing

    run_single_user(TestUser)