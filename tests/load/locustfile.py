"""
Locust Load Testing Script for CBSC Trading System
Python-based load testing with custom scenarios and metrics
"""

from locust import HttpUser, task, between
from locust.events import request_failure, request_success
import random
import json
import time
from datetime import datetime, timedelta

# Global metrics storage
metrics = {
    'total_requests': 0,
    'total_failures': 0,
    'response_times': [],
    'start_time': None
}

def on_request_success(request_type, name, response_time, response_length, **kwargs):
    """Handle successful requests"""
    metrics['total_requests'] += 1
    metrics['response_times'].append(response_time)

def on_request_failure(request_type, name, response_time, response_length, exception, **kwargs):
    """Handle failed requests"""
    metrics['total_requests'] += 1
    metrics['total_failures'] += 1
    metrics['response_times'].append(response_time)

# Register event handlers
request_success += on_request_success
request_failure += on_request_failure


class TradingSystemUser(HttpUser):
    """Simulated user behavior for the CBSC Trading System"""

    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts"""
        self.user_id = random.randint(1, 1000)
        self.strategy_id = random.randint(1, 10)
        self.session_id = f"session_{self.user_id}_{int(time.time())}"

        if not metrics['start_time']:
            metrics['start_time'] = time.time()

        # Login
        self.login()

    def login(self):
        """Authenticate user"""
        response = self.client.post("/api/auth/login", json={
            "username": f"user{self.user_id}",
            "password": "test123"
        })

        if response.status_code == 200:
            self.token = response.json().get('access_token')
            self.client.headers.update({
                'Authorization': f'Bearer {self.token}'
            })

    @task(3)
    def view_strategies(self):
        """View strategy list"""
        self.client.get("/api/strategies")

    @task(2)
    def view_strategy_details(self):
        """View specific strategy details"""
        self.client.get(f"/api/strategies/{self.strategy_id}")

    @task(1)
    def create_strategy(self):
        """Create a new strategy"""
        strategy_data = {
            "name": f"Strategy_{random.randint(1000, 9999)}",
            "description": "Automated strategy created during load test",
            "type": random.choice(["momentum", "mean_reversion", "arbitrage"]),
            "parameters": {
                "lookback_period": random.randint(10, 50),
                "threshold": round(random.uniform(0.01, 0.1), 3),
                "stop_loss": round(random.uniform(0.02, 0.1), 3),
                "take_profit": round(random.uniform(0.05, 0.2), 3)
            }
        }

        response = self.client.post("/api/strategies", json=strategy_data)

        if response.status_code == 201:
            # Store the new strategy ID for potential use
            self.new_strategy_id = response.json().get('id')

    @task(2)
    def get_performance_metrics(self):
        """Get real-time performance metrics"""
        self.client.get("/api/monitoring/performance")

    @task(2)
    def get_market_data(self):
        """Fetch market data"""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA"]
        selected_symbols = random.sample(symbols, k=random.randint(1, 5))

        params = {
            "symbols": ",".join(selected_symbols),
            "interval": random.choice(["1m", "5m", "15m", "1h", "1d"])
        }

        self.client.get("/api/market/data", params=params)

    @task(1)
    def run_backtest(self):
        """Run a backtest"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=random.randint(30, 365))

        backtest_data = {
            "strategy_id": self.strategy_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "initial_capital": random.choice([50000, 100000, 250000, 500000]),
            "commission": 0.001
        }

        response = self.client.post("/api/backtest/run", json=backtest_data)

        if response.status_code == 202:
            job_id = response.json().get('job_id')

            # Check status after a brief pause
            time.sleep(0.5)
            self.client.get(f"/api/backtest/status/{job_id}")

    @task(1)
    def get_active_trades(self):
        """Get list of active trades"""
        self.client.get("/api/trades/active")

    @task(1)
    def update_strategy_parameters(self):
        """Update strategy parameters"""
        if hasattr(self, 'new_strategy_id'):
            new_params = {
                "parameters": {
                    "lookback_period": random.randint(15, 60),
                    "threshold": round(random.uniform(0.015, 0.08), 3),
                    "stop_loss": round(random.uniform(0.025, 0.12), 3),
                    "take_profit": round(random.uniform(0.06, 0.25), 3)
                }
            }

            self.client.put(f"/api/strategies/{self.new_strategy_id}", json=new_params)

    @task(1)
    def get_portfolio_summary(self):
        """Get portfolio summary"""
        self.client.get("/api/portfolio/summary")

    @task(1)
    def execute_strategy(self):
        """Execute a strategy (simulate trade execution)"""
        # This would typically execute trades based on strategy signals
        execution_data = {
            "strategy_id": self.strategy_id,
            "symbol": random.choice(["AAPL", "GOOGL", "MSFT", "TSLA"]),
            "action": random.choice(["BUY", "SELL"]),
            "quantity": random.randint(10, 1000),
            "order_type": random.choice(["MARKET", "LIMIT"])
        }

        self.client.post("/api/trading/execute", json=execution_data)

    @task(1)
    def get_user_activity(self):
        """Get user activity log"""
        self.client.get(f"/api/users/{self.user_id}/activity")


class HighFrequencyUser(HttpUser):
    """High-frequency user for stress testing"""

    wait_time = between(0.1, 0.5)  # Very short wait times

    def on_start(self):
        self.user_id = random.randint(1, 1000)
        self.login()

    def login(self):
        """Quick login"""
        response = self.client.post("/api/auth/login", json={
            "username": f"hf_user{self.user_id}",
            "password": "test123"
        })

        if response.status_code == 200:
            self.token = response.json().get('access_token')
            self.client.headers.update({
                'Authorization': f'Bearer {self.token}'
            })

    @task(10)
    def get_real_time_data(self):
        """Constantly fetch real-time data"""
        self.client.get("/api/monitoring/performance")

    @task(5)
    def check_strategy_status(self):
        """Check strategy execution status"""
        self.client.get(f"/api/strategies/{random.randint(1, 10)}/status")


class WebSocketUser(HttpUser):
    """User testing WebSocket connections"""

    wait_time = between(5, 10)

    def on_start(self):
        self.user_id = random.randint(1, 1000)
        self.connect_websocket()

    def connect_websocket(self):
        """Establish WebSocket connection for real-time updates"""
        # Note: Locust doesn't directly support WebSockets
        # This would need to be implemented with a custom client
        pass

    @task(5)
    def subscribe_to_updates(self):
        """Subscribe to real-time updates"""
        self.client.post("/api/websocket/subscribe", json={
            "channels": ["strategy_updates", "market_data", "trade_executions"],
            "user_id": self.user_id
        })


# Export test statistics
def export_metrics():
    """Export test metrics to a file"""
    if metrics['response_times']:
        avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
        max_response_time = max(metrics['response_times'])
        min_response_time = min(metrics['response_times'])
    else:
        avg_response_time = max_response_time = min_response_time = 0

    report = {
        "test_summary": {
            "total_requests": metrics['total_requests'],
            "total_failures": metrics['total_failures'],
            "success_rate": ((metrics['total_requests'] - metrics['total_failures']) / metrics['total_requests'] * 100) if metrics['total_requests'] > 0 else 0,
            "avg_response_time_ms": avg_response_time * 1000,
            "max_response_time_ms": max_response_time * 1000,
            "min_response_time_ms": min_response_time * 1000,
            "test_duration_seconds": time.time() - metrics['start_time'] if metrics['start_time'] else 0
        },
        "timestamp": datetime.now().isoformat()
    }

    with open('locust-load-test-results.json', 'w') as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*50)
    print("📊 LOAD TEST SUMMARY")
    print("="*50)
    print(f"🔢 Total Requests: {report['test_summary']['total_requests']}")
    print(f"✅ Success Rate: {report['test_summary']['success_rate']:.2f}%")
    print(f"⏱️ Avg Response Time: {report['test_summary']['avg_response_time_ms']:.2f}ms")
    print(f"⚡ Max Response Time: {report['test_summary']['max_response_time_ms']:.2f}ms")
    print(f"📅 Test Duration: {report['test_summary']['test_duration_seconds']:.2f}s")
    print(f"💾 Results saved to: locust-load-test-results.json")

# Uncomment to run metrics export automatically
# import atexit
# atexit.register(export_metrics)