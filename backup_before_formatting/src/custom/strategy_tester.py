"""
策略测试框架
实现回测引擎集成、多时间段测试、性能指标计算和测试报告生成
"""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import rcParams

# 设置中文字体
rcParams["font.sans - seri"] = ["SimHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False

logger = logging.getLogger(__name__)


class TestType(Enum):
    """测试类型枚举"""

    BACKTEST = "backtest"
    PAPER_TRADING = "paper_trading"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"
    STRESS_TEST = "stress_test"


class TestStatus(Enum):
    """测试状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Trade:
    """交易记录"""

    timestamp: str
    symbol: str
    side: str  # BUY, SELL
    quantity: float
    price: float
    value: float
    commission: float = 0.0


@dataclass
class TestResult:
    """测试结果"""

    test_id: str
    test_type: TestType
    strategy_id: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    var_95: float  # Value at Risk
    trades: List[Trade]
    equity_curve: List[Dict]
    created_at: str


@dataclass
class TestConfig:
    """测试配置"""

    strategy_code: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    commission_rate: float = 0.0003  # 0.03%
    slippage: float = 0.0001  # 0.01%
    benchmark: str = "HSI"
    risk_free_rate: float = 0.02  # 2%


class StrategyTester:
    """策略测试器核心类"""

    def __init__(self, db_path: str = "data / strategy_tests.db"):
        """初始化测试器"""
        self.db_path = db_path
        self.test_results: Dict[str, TestResult] = {}
        self._init_database()

    def _init_database(self):
        """初始化SQLite数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_results (
                test_id TEXT PRIMARY KEY,
                test_type TEXT NOT NULL,
                strategy_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                final_capital REAL NOT NULL,
                total_return REAL NOT NULL,
                annualized_return REAL NOT NULL,
                volatility REAL NOT NULL,
                sharpe_ratio REAL NOT NULL,
                max_drawdown REAL NOT NULL,
                win_rate REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                winning_trades INTEGER NOT NULL,
                losing_trades INTEGER NOT NULL,
                avg_win REAL NOT NULL,
                avg_loss REAL NOT NULL,
                profit_factor REAL NOT NULL,
                var_95 REAL NOT NULL,
                trades_json TEXT,
                equity_curve_json TEXT,
                created_at TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

    def run_backtest(
        self, config: TestConfig, data_source: str = "yahoo"
    ) -> TestResult:
        """运行回测"""
        test_id = f"bt_{datetime.now().strftime('%Y % m % d_ % H % M % S')}_{config.symbol}"
        logger.info(f"开始回测: {test_id}")

        try:
            # 获取数据
            data = self._fetch_data(
                config.symbol, config.start_date, config.end_date, data_source
            )
            if data is None or data.empty:
                raise ValueError(f"无法获取数据: {config.symbol}")

            # 执行策略
            trades, signals = self._execute_strategy(config.strategy_code, data, config)

            # 计算性能指标
            result = self._calculate_metrics(
                test_id=test_id,
                test_type=TestType.BACKTEST,
                strategy_id=config.strategy_code,
                data=data,
                trades=trades,
                config=config,
            )

            # 保存结果
            self._save_result(result)
            self.test_results[test_id] = result

            logger.info(f"回测完成: {test_id}, 收益率: {result.total_return:.2%}")
            return result

        except Exception as e:
            logger.error(f"回测失败: {test_id}, {e}")
            raise

    def run_walk_forward(
        self,
        config: TestConfig,
        train_period: int = 252,  # 1年
        test_period: int = 63,  # 3个月
        step: int = 21,
    ) -> List[TestResult]:
        """运行前进分析"""
        logger.info(f"开始前进分析: {config.symbol}")

        results = []
        start_date = pd.to_datetime(config.start_date)
        end_date = pd.to_datetime(config.end_date)

        current_start = start_date
        iteration = 0

        while current_start + timedelta(days=train_period + test_period) <= end_date:
            train_end = current_start + timedelta(days=train_period)
            test_end = train_end + timedelta(days=test_period)

            # 训练期
            train_config = TestConfig(
                strategy_code=config.strategy_code,
                symbol=config.symbol,
                start_date=current_start.strftime("%Y-%m-%d"),
                end_date=train_end.strftime("%Y-%m-%d"),
                initial_capital=config.initial_capital,
                commission_rate=config.commission_rate,
                slippage=config.slippage,
            )

            # 测试期
            test_start = train_end + timedelta(days=1)
            test_config = TestConfig(
                strategy_code=config.strategy_code,
                symbol=config.symbol,
                start_date=test_start.strftime("%Y-%m-%d"),
                end_date=test_end.strftime("%Y-%m-%d"),
                initial_capital=config.initial_capital,
                commission_rate=config.commission_rate,
                slippage=config.slippage,
            )

            try:
                # 训练模型（这里简化处理）
                logger.info(
                    f"第 {iteration + 1} 轮训练: {train_config.start_date} ~ {train_config.end_date}"
                )

                # 测试
                result = self.run_backtest(test_config)
                results.append(result)

                logger.info(f"第 {iteration + 1} 轮测试完成: {result.total_return:.2%}")

            except Exception as e:
                logger.error(f"第 {iteration + 1} 轮失败: {e}")
                continue

            current_start += timedelta(days=step)
            iteration += 1

        logger.info(f"前进分析完成，共 {len(results)} 轮测试")
        return results

    def run_monte_carlo(
        self,
        config: TestConfig,
        num_simulations: int = 1000,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """运行蒙特卡洛模拟"""
        logger.info(f"开始蒙特卡洛模拟: {config.symbol}, 次数: {num_simulations}")

        try:
            # 获取原始数据
            data = self._fetch_data(config.symbol, config.start_date, config.end_date)
            if data is None or data.empty:
                raise ValueError(f"无法获取数据: {config.symbol}")

            returns = data["close"].pct_change().dropna()

            # 生成模拟路径
            simulated_results = []
            for i in range(num_simulations):
                # 随机抽样（自助法）
                sampled_returns = np.random.choice(
                    returns.values, size=len(returns), replace=True
                )

                # 构建价格路径
                initial_price = data["close"].iloc[0]
                prices = [initial_price]
                for r in sampled_returns:
                    prices.append(prices[-1] * (1 + r))

                # 计算收益率
                total_return = (prices[-1] - initial_price) / initial_price
                simulated_results.append(total_return)

            # 计算统计指标
            simulated_results = np.array(simulated_results)
            mean_return = np.mean(simulated_results)
            std_return = np.std(simulated_results)
            var_5 = np.percentile(simulated_results, 5)
            var_1 = np.percentile(simulated_results, 1)

            # 计算VaR
            var_95 = np.percentile(simulated_results, (1 - confidence_level) * 100)

            # 计算置信区间
            ci_lower = np.percentile(
                simulated_results, (1 - confidence_level) / 2 * 100
            )
            ci_upper = np.percentile(
                simulated_results, (1 + confidence_level) / 2 * 100
            )

            result = {
                "test_id": f"mc_{datetime.now().strftime('%Y % m % d_ % H % M % S')}",
                "test_type": TestType.MONTE_CARLO,
                "num_simulations": num_simulations,
                "mean_return": mean_return,
                "std_return": std_return,
                "var_95": var_95,
                "var_99": var_1,
                "confidence_interval": (ci_lower, ci_upper),
                "min_return": np.min(simulated_results),
                "max_return": np.max(simulated_results),
                "prob_positive": np.mean(simulated_results > 0),
                "results_distribution": simulated_results.tolist(),
            }

            logger.info(f"蒙特卡洛模拟完成，平均收益率: {mean_return:.2%}")
            return result

        except Exception as e:
            logger.error(f"蒙特卡洛模拟失败: {e}")
            raise

    def _fetch_data(
        self, symbol: str, start_date: str, end_date: str, source: str = "yahoo"
    ) -> Optional[pd.DataFrame]:
        """获取数据（简化版）"""
        try:
            # 尝试使用项目的数据源
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)

            if data.empty:
                return None

            # 确保有必要的列
            if not all(
                col in data.columns
                for col in ["Open", "High", "Low", "Close", "Volume"]
            ):
                data.columns = ["Open", "High", "Low", "Close", "Volume"]

            return data.rename(
                columns={"Close": "close", "Open": "open", "High": "high", "Low": "low"}
            )

        except Exception as e:
            logger.warning(f"无法从 {source} 获取数据: {e}")
            # 生成模拟数据用于演示
            return self._generate_sample_data(symbol, start_date, end_date)

    def _generate_sample_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """生成示例数据"""
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        dates = dates[dates.weekday < 5]  # 排除周末

        np.random.seed(42)
        n = len(dates)

        # 生成随机游走数据
        returns = np.random.normal(0.0005, 0.02, n)
        prices = [100.0]
        for r in returns:
            prices.append(prices[-1] * (1 + r))

        prices = prices[1:]

        data = pd.DataFrame(
            {
                "open": prices,
                "high": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                "low": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                "close": prices,
                "volume": np.random.randint(1000000, 10000000, n),
            },
            index=dates,
        )

        return data

    def _execute_strategy(
        self, strategy_code: str, data: pd.DataFrame, config: TestConfig
    ) -> Tuple[List[Trade], List[Dict]]:
        """执行策略"""
        trades = []
        signals = []
        position = 0
        entry_price = 0.0

        # 动态执行策略代码
        local_vars = {
            "data": data,
            "config": config,
            "trades": trades,
            "signals": signals,
        }

        try:
            # 创建一个简化的策略执行环境
            exec(strategy_code, {"__builtins__": {}}, local_vars)
            return local_vars.get("trades", []), local_vars.get("signals", [])

        except Exception as e:
            logger.error(f"策略执行失败: {e}")
            # 返回简单的买入持有策略
            return self._simple_buy_hold_strategy(data, config)

    def _simple_buy_hold_strategy(
        self, data: pd.DataFrame, config: TestConfig
    ) -> Tuple[List[Trade], List[Dict]]:
        """简单的买入持有策略"""
        trades = []
        signals = []

        # 第一天买入
        first_day = data.index[0]
        price = data["close"].iloc[0]
        quantity = config.initial_capital / price * 0.95  # 95 % 资金

        trades.append(
            Trade(
                timestamp=first_day.strftime("%Y-%m-%d"),
                symbol=config.symbol,
                side="BUY",
                quantity=quantity,
                price=price,
                value=quantity * price,
                commission=quantity * price * config.commission_rate,
            )
        )

        # 最后一天卖出
        last_day = data.index[-1]
        price = data["close"].iloc[-1]

        trades.append(
            Trade(
                timestamp=last_day.strftime("%Y-%m-%d"),
                symbol=config.symbol,
                side="SELL",
                quantity=quantity,
                price=price,
                value=quantity * price,
                commission=quantity * price * config.commission_rate,
            )
        )

        return trades, []

    def _calculate_metrics(
        self,
        test_id: str,
        test_type: TestType,
        strategy_id: str,
        data: pd.DataFrame,
        trades: List[Trade],
        config: TestConfig,
    ) -> TestResult:
        """计算性能指标"""
        # 构建资金曲线
        equity_curve = self._build_equity_curve(data, trades, config)
        equity_values = [p["value"] for p in equity_curve]

        # 基本指标
        initial_capital = config.initial_capital
        final_capital = equity_values[-1] if equity_values else initial_capital
        total_return = (final_capital - initial_capital) / initial_capital

        # 计算年化收益率
        days = (pd.to_datetime(data.index[-1]) - pd.to_datetime(data.index[0])).days
        years = days / 365.25
        annualized_return = (
            (final_capital / initial_capital) ** (1 / years) - 1 if years > 0 else 0
        )

        # 计算波动率
        returns = pd.Series(equity_values).pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)

        # 计算夏普比率
        excess_return = annualized_return - config.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0

        # 计算最大回撤
        peak = np.maximum.accumulate(equity_values)
        drawdown = (np.array(equity_values) - peak) / peak
        max_drawdown = np.min(drawdown)

        # 交易统计
        buy_trades = [t for t in trades if t.side == "BUY"]
        sell_trades = [t for t in trades if t.side == "SELL"]

        winning_trades = 0
        losing_trades = 0
        total_wins = 0
        total_losses = 0

        for i in range(0, len(trades), 2):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]
                pnl = (sell_trade.price - buy_trade.price) * buy_trade.quantity

                if pnl > 0:
                    winning_trades += 1
                    total_wins += pnl
                else:
                    losing_trades += 1
                    total_losses += abs(pnl)

        win_rate = (
            winning_trades / (winning_trades + losing_trades)
            if (winning_trades + losing_trades) > 0
            else 0
        )
        avg_win = total_wins / winning_trades if winning_trades > 0 else 0
        avg_loss = total_losses / losing_trades if losing_trades > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

        # 计算VaR
        var_95 = np.percentile(returns, 5)

        return TestResult(
            test_id=test_id,
            test_type=test_type,
            strategy_id=strategy_id,
            start_date=data.index[0].strftime("%Y-%m-%d"),
            end_date=data.index[-1].strftime("%Y-%m-%d"),
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=len(trades) // 2,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            var_95=var_95,
            trades=trades,
            equity_curve=equity_curve,
            created_at=datetime.now().isoformat(),
        )

    def _build_equity_curve(
        self, data: pd.DataFrame, trades: List[Trade], config: TestConfig
    ) -> List[Dict]:
        """构建资金曲线"""
        equity_curve = []
        capital = config.initial_capital
        position = 0

        for date, row in data.iterrows():
            date_str = date.strftime("%Y-%m-%d")

            # 检查是否有交易
            for trade in trades:
                if trade.timestamp == date_str:
                    if trade.side == "BUY":
                        position += trade.quantity
                        capital -= trade.value + trade.commission
                    else:
                        position -= trade.quantity
                        capital += trade.value - trade.commission

            # 计算当前总资产
            current_value = capital + position * row["close"]
            equity_curve.append(
                {
                    "date": date_str,
                    "value": current_value,
                    "position": position,
                    "capital": capital,
                }
            )

        return equity_curve

    def _save_result(self, result: TestResult):
        """保存测试结果到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO test_results
            (test_id, test_type, strategy_id, start_date, end_date,
             initial_capital, final_capital, total_return, annualized_return,
             volatility, sharpe_ratio, max_drawdown, win_rate, total_trades,
             winning_trades, losing_trades, avg_win, avg_loss, profit_factor,
             var_95, trades_json, equity_curve_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result.test_id,
                result.test_type.value,
                result.strategy_id,
                result.start_date,
                result.end_date,
                result.initial_capital,
                result.final_capital,
                result.total_return,
                result.annualized_return,
                result.volatility,
                result.sharpe_ratio,
                result.max_drawdown,
                result.win_rate,
                result.total_trades,
                result.winning_trades,
                result.losing_trades,
                result.avg_win,
                result.avg_loss,
                result.profit_factor,
                result.var_95,
                json.dumps([asdict(t) for t in result.trades]),
                json.dumps(result.equity_curve),
                result.created_at,
            ),
        )

        conn.commit()
        conn.close()

    def get_test_result(self, test_id: str) -> Optional[TestResult]:
        """获取测试结果"""
        return self.test_results.get(test_id)

    def list_tests(
        self, test_type: TestType = None, strategy_id: str = None, limit: int = 100
    ) -> List[TestResult]:
        """列出测试结果"""
        results = list(self.test_results.values())

        if test_type:
            results = [r for r in results if r.test_type == test_type]

        if strategy_id:
            results = [r for r in results if r.strategy_id == strategy_id]

        return sorted(results, key=lambda r: r.created_at, reverse=True)[:limit]

    def generate_report(self, test_id: str, output_path: str = None) -> str:
        """生成测试报告"""
        result = self.get_test_result(test_id)
        if not result:
            raise ValueError(f"测试结果不存在: {test_id}")

        if not output_path:
            output_path = f"data / reports / test_report_{test_id}.html"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 生成HTML报告
        html = self._create_html_report(result)

        with open(output_path, "w", encoding="utf - 8") as f:
            f.write(html)

        logger.info(f"测试报告已生成: {output_path}")
        return output_path

    def _create_html_report(self, result: TestResult) -> str:
        """创建HTML报告"""
        html = """
<!DOCTYPE html>
<html lang="zh - CN">
<head>
    <meta charset="UTF - 8">
    <meta name="viewport" content="width=device - width, initial - scale=1.0">
    <title>策略测试报告 - {result.test_id}</title>
    <style>
        body {{ font - family: 'Arial', sans - serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max - width: 1200px; margin: 0 auto; background: white; padding: 20px; border - radius: 8px; }}
        h1 {{ color: #2c3e50; border - bottom: 3px solid #3498db; padding - bottom: 10px; }}
        h2 {{ color: #34495e; margin - top: 30px; }}
        .metrics {{ display: grid; grid - template - columns: repeat(auto - fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric - card {{ background: linear - gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border - radius: 8px; text - align: center; }}
        .metric - value {{ font - size: 24px; font - weight: bold; margin: 5px 0; }}
        .metric - label {{ font - size: 14px; opacity: 0.9; }}
        .positive {{ color: #2ecc71; }}
        .negative {{ color: #e74c3c; }}
        table {{ width: 100%; border - collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text - align: left; border - bottom: 1px solid #ddd; }}
        th {{ background - color: #3498db; color: white; }}
        tr:hover {{ background - color: #f5f5f5; }}
        .chart {{ margin: 20px 0; text - align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>策略测试报告</h1>
        <p><strong>测试ID:</strong> {result.test_id}</p>
        <p><strong>测试类型:</strong> {result.test_type.value}</p>
        <p><strong>策略ID:</strong> {result.strategy_id}</p>
        <p><strong>测试期间:</strong> {result.start_date} ~ {result.end_date}</p>
        <p><strong>报告生成时间:</strong> {result.created_at}</p>

        <h2>核心指标</h2>
        <div class="metrics">
            <div class="metric - card">
                <div class="metric - label">总收益率</div>
                <div class="metric - value {'positive' if result.total_return > 0 else 'negative'}">{result.total_return:.2%}</div>
            </div>
            <div class="metric - card">
                <div class="metric - label">年化收益率</div>
                <div class="metric - value {'positive' if result.annualized_return > 0 else 'negative'}">{result.annualized_return:.2%}</div>
            </div>
            <div class="metric - card">
                <div class="metric - label">夏普比率</div>
                <div class="metric - value">{result.sharpe_ratio:.2f}</div>
            </div>
            <div class="metric - card">
                <div class="metric - label">最大回撤</div>
                <div class="metric - value negative">{result.max_drawdown:.2%}</div>
            </div>
            <div class="metric - card">
                <div class="metric - label">波动率</div>
                <div class="metric - value">{result.volatility:.2%}</div>
            </div>
            <div class="metric - card">
                <div class="metric - label">胜率</div>
                <div class="metric - value">{result.win_rate:.2%}</div>
            </div>
        </div>

        <h2>交易统计</h2>
        <table>
            <tr><th>总交易次数</th><td>{result.total_trades}</td></tr>
            <tr><th>盈利交易</th><td class="positive">{result.winning_trades}</td></tr>
            <tr><th>亏损交易</th><td class="negative">{result.losing_trades}</td></tr>
            <tr><th>平均盈利</th><td class="positive">{result.avg_win:.2f}</td></tr>
            <tr><th>平均亏损</th><td class="negative">{result.avg_loss:.2f}</td></tr>
            <tr><th>盈亏比</th><td>{result.profit_factor:.2f}</td></tr>
            <tr><th>95% VaR</th><td>{result.var_95:.4f}</td></tr>
        </table>

        <h2>资金曲线</h2>
        <div class="chart">
            <p>资金曲线数据点: {len(result.equity_curve)}</p>
        </div>

        <h2>交易记录</h2>
        <table>
            <tr>
                <th>时间</th>
                <th>方向</th>
                <th>数量</th>
                <th>价格</th>
                <th>价值</th>
            </tr>
        """

        for trade in result.trades:
            html += """
            <tr>
                <td>{trade.timestamp}</td>
                <td>{trade.side}</td>
                <td>{trade.quantity:.2f}</td>
                <td>{trade.price:.2f}</td>
                <td>{trade.value:.2f}</td>
            </tr>
            """

        html += """
        </table>
    </div>
</body>
</html>
        """

        return html

    def compare_strategies(self, test_ids: List[str]) -> Dict[str, Any]:
        """比较多个策略"""
        results = [self.get_test_result(tid) for tid in test_ids]
        results = [r for r in results if r is not None]

        if len(results) < 2:
            raise ValueError("至少需要2个测试结果进行比较")

        comparison = {
            "metrics": {
                "total_return": {r.test_id: r.total_return for r in results},
                "annualized_return": {r.test_id: r.annualized_return for r in results},
                "sharpe_ratio": {r.test_id: r.sharpe_ratio for r in results},
                "max_drawdown": {r.test_id: r.max_drawdown for r in results},
                "win_rate": {r.test_id: r.win_rate for r in results},
                "total_trades": {r.test_id: r.total_trades for r in results},
            },
            "best_by_metric": {
                "return": max(results, key=lambda r: r.total_return).test_id,
                "sharpe": max(results, key=lambda r: r.sharpe_ratio).test_id,
                "drawdown": min(results, key=lambda r: r.max_drawdown).test_id,
                "win_rate": max(results, key=lambda r: r.win_rate).test_id,
            },
        }

        return comparison
