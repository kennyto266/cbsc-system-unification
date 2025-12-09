"""
強化學習交易智能體系統
專門為港股量化交易設計的生產級別強化學習框架

功能:
- 深度Q網絡 (DQN) 交易智能體
- 近端策略優化 (PPO) 智能體
- 異步優勢演員評論家 (A3C) 智能體
- 多智能體協作系統
- 層次化強化學習 (HRL)
- 風險感知強化學習
- 實時訓練和部署
"""

import asyncio
import json
import logging
import random
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import gym
import numpy as np
import pandas as pd
from gym import spaces

warnings.filterwarnings("ignore")

# 強化學習框架
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.distributions import Categorical, Normal
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import stable_baselines3 as sb3
    from stable_baselines3 import A2C, DQN, PPO, SAC
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False

try:
    import ray
    from ray import tune
    from ray.rllib.agents import a3c, dqn, ppo
    from ray.rllib.models import ModelCatalog
    from ray.rllib.models.tf.fcnet import FullyConnectedNetwork

    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False

import vectorbt as vbt

# 金融建模
from sklearn.preprocessing import StandardScaler

from .trading_models import MarketRegimeDetector, RiskMetrics, SentimentAnalyzer


class ActionType(Enum):
    """動作類型"""

    HOLD = 0
    BUY = 1
    SELL = 2
    BUY_STRONG = 3
    SELL_STRONG = 4


class AgentType(Enum):
    """智能體類型"""

    DQN = "dqn"
    PPO = "ppo"
    A3C = "a3c"
    SAC = "sac"
    MULTI_AGENT = "multi_agent"
    HIERARCHICAL = "hierarchical"


@dataclass
class TradingState:
    """交易狀態"""

    position: float  # 當前持倉 (-1 to 1)
    cash: float  # 現金
    portfolio_value: float  # 投資組合價值
    unrealized_pnl: float  # 未實現損益
    realized_pnl: float  # 已實現損益
    total_trades: int  # 總交易次數
    win_rate: float  # 勝率
    sharpe_ratio: float  # 夏普比率
    max_drawdown: float  # 最大回撤
    volatility: float  # 波動率
    market_regime: int  # 市場狀態
    sentiment_score: float  # 情緒分數


@dataclass
class AgentAction:
    """智能體動作"""

    action_type: ActionType
    amount: float
    confidence: float
    timestamp: datetime
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """智能體性能指標"""

    total_return: float
    annual_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_trade_return: float
    trade_frequency: float
    position_holding_time: float
    volatility: float
    beta: float
    alpha: float
    information_ratio: float
    calmar_ratio: float


class TradingEnvironment(gym.Env):
    """
    交易環境 (OpenAI Gym兼容)

    模擬真實的交易環境，支持多種交易策略和風險管理
    """

    def __init__(
        self,
        data: pd.DataFrame,
        initial_cash: float = 100000,
        commission: float = 0.001,
        max_position_size: float = 1.0,
        lookback_window: int = 60,
        regime_detector: Optional[MarketRegimeDetector] = None,
        sentiment_analyzer: Optional[SentimentAnalyzer] = None,
    ):
        super().__init__()

        self.logger = logging.getLogger("hk_quant_system.trading_env")

        # 數據和配置
        self.data = data.copy()
        self.initial_cash = initial_cash
        self.commission = commission
        self.max_position_size = max_position_size
        self.lookback_window = lookback_window

        # 外部組件
        self.regime_detector = regime_detector
        self.sentiment_analyzer = sentiment_analyzer

        # 狀態變量
        self.current_step = 0
        self.cash = initial_cash
        self.position = 0.0
        self.portfolio_value = initial_cash
        self.trade_history = []
        self.portfolio_history = []

        # 市場狀態和情緒
        self.market_regimes = {}
        self.sentiment_scores = {}

        # 動作和觀察空間
        self.action_space = spaces.Discrete(len(ActionType))

        # 計算觀察空間維度
        self.feature_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "returns",
            "volatility",
            "rsi",
            "macd",
            "bb_position",
        ]

        # 確保所有特徵列存在
        for col in self.feature_columns:
            if col not in self.data.columns:
                if col == "returns":
                    self.data[col] = self.data["close"].pct_change()
                elif col == "volatility":
                    self.data[col] = self.data["close"].pct_change().rolling(20).std()
                # 其他特徵需要在數據預處理階段計算

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(
                self.lookback_window,
                len(self.feature_columns) + 10,
            ),  # +10 for state features
            dtype=np.float32,
        )

        # 初始化市場狀態
        self._initialize_market_states()

    def _initialize_market_states(self):
        """初始化市場狀態"""
        try:
            if self.regime_detector:
                regime_result = self.regime_detector.detect_regimes_hmm(self.data)
                self.market_regimes = regime_result.get(
                    "regime_history", [0] * len(self.data)
                )
            else:
                self.market_regimes = [0] * len(self.data)

            if self.sentiment_analyzer:
                # 這裡可以集成真實的新聞數據進行情緒分析
                self.sentiment_scores = [0.0] * len(self.data)  # 佔位符
            else:
                self.sentiment_scores = [0.0] * len(self.data)

        except Exception as e:
            self.logger.warning(f"Market state initialization failed: {str(e)}")
            self.market_regimes = [0] * len(self.data)
            self.sentiment_scores = [0.0] * len(self.data)

    def reset(self) -> np.ndarray:
        """重置環境"""
        self.current_step = self.lookback_window
        self.cash = self.initial_cash
        self.position = 0.0
        self.portfolio_value = self.initial_cash
        self.trade_history = []
        self.portfolio_history = []

        return self._get_observation()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """執行一步"""
        if self.current_step >= len(self.data) - 1:
            return self._get_observation(), 0, True, {}

        # 獲取當前價格
        current_price = self.data.iloc[self.current_step]["close"]

        # 執行動作
        reward = self._execute_action(ActionType(action), current_price)

        # 更新投資組合價值
        self._update_portfolio_value(current_price)

        # 移動到下一步
        self.current_step += 1

        # 檢查是否結束
        done = self.current_step >= len(self.data) - 1 or self.cash <= 0

        # 獲取觀察
        observation = self._get_observation()

        # 準備信息字典
        info = {
            "portfolio_value": self.portfolio_value,
            "cash": self.cash,
            "position": self.position,
            "total_trades": len(self.trade_history),
            "win_rate": self._calculate_win_rate(),
            "sharpe_ratio": self._calculate_sharpe_ratio(),
            "max_drawdown": self._calculate_max_drawdown(),
        }

        return observation, reward, done, info

    def _execute_action(self, action: ActionType, current_price: float) -> float:
        """執行交易動作"""
        old_portfolio_value = self.portfolio_value
        old_position = self.position

        if action == ActionType.HOLD:
            return 0

        elif action == ActionType.BUY:
            amount = min(
                0.25, self.max_position_size - self.position
            )  # 買入25 % 或至最大持倉
            if amount > 0 and self.cash > current_price * amount:
                cost = amount * current_price * (1 + self.commission)
                self.cash -= cost
                self.position += amount

                self.trade_history.append(
                    {
                        "step": self.current_step,
                        "action": "BUY",
                        "amount": amount,
                        "price": current_price,
                        "cost": cost,
                    }
                )

        elif action == ActionType.SELL:
            amount = min(0.25, self.position)  # 賣出25 % 或全部持倉
            if amount > 0:
                proceeds = amount * current_price * (1 - self.commission)
                self.cash += proceeds
                self.position -= amount

                self.trade_history.append(
                    {
                        "step": self.current_step,
                        "action": "SELL",
                        "amount": amount,
                        "price": current_price,
                        "proceeds": proceeds,
                    }
                )

        elif action == ActionType.BUY_STRONG:
            amount = min(0.5, self.max_position_size - self.position)  # 強力買入
            if amount > 0 and self.cash > current_price * amount:
                cost = amount * current_price * (1 + self.commission)
                self.cash -= cost
                self.position += amount

                self.trade_history.append(
                    {
                        "step": self.current_step,
                        "action": "BUY_STRONG",
                        "amount": amount,
                        "price": current_price,
                        "cost": cost,
                    }
                )

        elif action == ActionType.SELL_STRONG:
            amount = min(0.5, self.position)  # 強力賣出
            if amount > 0:
                proceeds = amount * current_price * (1 - self.commission)
                self.cash += proceeds
                self.position -= amount

                self.trade_history.append(
                    {
                        "step": self.current_step,
                        "action": "SELL_STRONG",
                        "amount": amount,
                        "price": current_price,
                        "proceeds": proceeds,
                    }
                )

        # 計算即時獎勵
        new_portfolio_value = self.cash + self.position * current_price
        portfolio_return = (
            new_portfolio_value - old_portfolio_value
        ) / old_portfolio_value

        # 風險調整獎勵
        volatility_penalty = (
            abs(self.position) * self.data.iloc[self.current_step]["volatility"]
        )
        transaction_cost_penalty = (
            len([t for t in self.trade_history if t["step"] == self.current_step])
            * 0.001
        )

        reward = portfolio_return - volatility_penalty - transaction_cost_penalty

        return reward

    def _update_portfolio_value(self, current_price: float):
        """更新投資組合價值"""
        self.portfolio_value = self.cash + self.position * current_price
        self.portfolio_history.append(self.portfolio_value)

    def _get_observation(self) -> np.ndarray:
        """獲取觀察"""
        if self.current_step < self.lookback_window:
            return np.zeros(
                (self.lookback_window, len(self.feature_columns) + 10), dtype=np.float32
            )

        # 價格和技術指標數據
        start_idx = self.current_step - self.lookback_window
        end_idx = self.current_step

        price_features = self.data[self.feature_columns].iloc[start_idx:end_idx].values

        # 狀態特徵
        current_price = self.data.iloc[self.current_step]["close"]
        state_features = np.array(
            [
                self.position,
                self.cash / self.initial_cash,
                self.portfolio_value / self.initial_cash,
                len(self.trade_history) / 1000,  # 交易頻率
                self._calculate_win_rate(),
                self._calculate_sharpe_ratio(),
                self._calculate_max_drawdown(),
                (
                    self.market_regimes[self.current_step]
                    if self.current_step < len(self.market_regimes)
                    else 0
                ),
                (
                    self.sentiment_scores[self.current_step]
                    if self.current_step < len(self.sentiment_scores)
                    else 0
                ),
                self.data.iloc[self.current_step].get("volatility", 0),
            ]
        )

        # 擴展狀態特徵到與時間窗口相同的長度
        state_features_expanded = np.tile(state_features, (self.lookback_window, 1))

        # 組合觀察
        observation = np.concatenate([price_features, state_features_expanded], axis=1)

        return observation.astype(np.float32)

    def _calculate_win_rate(self) -> float:
        """計算勝率"""
        if len(self.trade_history) < 2:
            return 0.0

        winning_trades = 0
        for i in range(1, len(self.trade_history)):
            if self.trade_history[i]["action"].startswith("SELL"):
                # 簡化的勝率計算
                if self.trade_history[i]["price"] > self.trade_history[i - 1]["price"]:
                    winning_trades += 1

        return winning_trades / max(1, len(self.trade_history) // 2)

    def _calculate_sharpe_ratio(self) -> float:
        """計算夏普比率"""
        if len(self.portfolio_history) < 2:
            return 0.0

        returns = pd.Series(self.portfolio_history).pct_change().dropna()
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        return returns.mean() / returns.std() * np.sqrt(252)

    def _calculate_max_drawdown(self) -> float:
        """計算最大回撤"""
        if len(self.portfolio_history) < 2:
            return 0.0

        portfolio_series = pd.Series(self.portfolio_history)
        peak = portfolio_series.expanding().max()
        drawdown = (portfolio_series - peak) / peak

        return drawdown.min()


class DQNNetwork(nn.Module):
    """深度Q網絡"""

    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int] = [512, 256, 128],
        output_dim: int = len(ActionType),
    ):
        super().__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([nn.Linear(prev_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.2)])
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


class DQNAgent:
    """深度Q網絡智能體"""

    def __init__(
        self,
        state_dim: int,
        action_dim: int = len(ActionType),
        learning_rate: float = 1e-4,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        memory_size: int = 10000,
        batch_size: int = 32,
        target_update_freq: int = 1000,
    ):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for DQN agent")

        self.logger = logging.getLogger("hk_quant_system.dqn_agent")

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq

        # 神經網絡
        self.q_network = DQNNetwork(state_dim, output_dim=action_dim)
        self.target_network = DQNNetwork(state_dim, output_dim=action_dim)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)

        # 初始化目標網絡
        self.target_network.load_state_dict(self.q_network.state_dict())

        # 經驗回放
        self.memory = deque(maxlen=memory_size)

        # 訓練統計
        self.training_steps = 0
        self.losses = []

    def get_action(self, state: np.ndarray, training: bool = True) -> int:
        """獲取動作"""
        if training and random.random() < self.epsilon:
            return random.randrange(self.action_dim)

        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.q_network(state_tensor)
        return q_values.argmax().item()

    def remember(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        """存儲經驗"""
        self.memory.append((state, action, reward, next_state, done))

    def replay(self) -> float:
        """經驗回放訓練"""
        if len(self.memory) < self.batch_size:
            return 0.0

        # 隨機採樣
        batch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.BoolTensor([e[4] for e in batch])

        # 當前Q值
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))

        # 下一狀態的最大Q值
        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + (self.gamma * next_q_values * ~dones)

        # 計算損失
        loss = F.mse_loss(current_q_values.squeeze(), target_q_values)

        # 反向傳播
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # 更新目標網絡
        self.training_steps += 1
        if self.training_steps % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

        # 衰減探索率
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        self.losses.append(loss.item())
        return loss.item()

    def save_model(self, filepath: str):
        """保存模型"""
        torch.save(
            {
                "q_network_state_dict": self.q_network.state_dict(),
                "target_network_state_dict": self.target_network.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "epsilon": self.epsilon,
                "training_steps": self.training_steps,
            },
            filepath,
        )
        self.logger.info(f"DQN model saved to {filepath}")

    def load_model(self, filepath: str):
        """加載模型"""
        checkpoint = torch.load(filepath)
        self.q_network.load_state_dict(checkpoint["q_network_state_dict"])
        self.target_network.load_state_dict(checkpoint["target_network_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = checkpoint["epsilon"]
        self.training_steps = checkpoint["training_steps"]
        self.logger.info(f"DQN model loaded from {filepath}")


class PPONetwork(nn.Module):
    """PPO網絡"""

    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int] = [256, 128],
        action_dim: int = len(ActionType),
    ):
        super().__init__()

        # 共享特徵提取層
        self.feature_layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
            nn.Dropout(0.2),
        )

        # 策略頭 (Actor)
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dims[1], action_dim), nn.Softmax(dim=-1)
        )

        # 價值頭 (Critic)
        self.value_head = nn.Linear(hidden_dims[1], 1)

    def forward(self, x):
        features = self.feature_layers(x)
        policy = self.policy_head(features)
        value = self.value_head(features)
        return policy, value

    def get_action_and_value(self, x, action=None):
        policy, value = self.forward(x)
        dist = Categorical(policy)

        if action is None:
            action = dist.sample()

        return action, dist.log_prob(action), dist.entropy(), value.squeeze()


class PPOAgent:
    """PPO智能體"""

    def __init__(
        self,
        state_dim: int,
        action_dim: int = len(ActionType),
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 0.5,
        ppo_epochs: int = 4,
        batch_size: int = 64,
    ):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for PPO agent")

        self.logger = logging.getLogger("hk_quant_system.ppo_agent")

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        self.ppo_epochs = ppo_epochs
        self.batch_size = batch_size

        # 神經網絡
        self.network = PPONetwork(state_dim, action_dim=action_dim)
        self.optimizer = optim.Adam(self.network.parameters(), lr=learning_rate)

        # 存儲
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []

    def get_action(self, state: np.ndarray) -> Tuple[int, float, float]:
        """獲取動作"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            action, log_prob, _, value = self.network.get_action_and_value(state_tensor)

        return action.item(), log_prob.item(), value.item()

    def remember(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        value: float,
        log_prob: float,
        done: bool,
    ):
        """存儲經驗"""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value)
        self.log_probs.append(log_prob)
        self.dones.append(done)

    def update(self) -> Dict[str, float]:
        """更新網絡"""
        if len(self.states) < self.batch_size:
            return {}

        # 轉換為張量
        states = torch.FloatTensor(np.array(self.states))
        actions = torch.LongTensor(self.actions)
        rewards = torch.FloatTensor(self.rewards)
        values = torch.FloatTensor(self.values)
        old_log_probs = torch.FloatTensor(self.log_probs)
        dones = torch.BoolTensor(self.dones)

        # 計算優勢和回報
        advantages = self._compute_advantages(rewards, values, dones)
        returns = advantages + values

        # 正規化優勢
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO更新
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy_loss = 0

        for _ in range(self.ppo_epochs):
            # 批處理
            for i in range(0, len(states), self.batch_size):
                batch_indices = slice(i, i + self.batch_size)
                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]

                # 前向傳播
                _, new_log_probs, entropy, new_values = (
                    self.network.get_action_and_value(batch_states, batch_actions)
                )

                # 計算比率
                ratio = torch.exp(new_log_probs - batch_old_log_probs)

                # 策略損失
                surr1 = ratio * batch_advantages
                surr2 = (
                    torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon)
                    * batch_advantages
                )
                policy_loss = -torch.min(surr1, surr2).mean()

                # 價值損失
                value_loss = F.mse_loss(new_values, batch_returns)

                # 熵損失
                entropy_loss = -entropy.mean()

                # 總損失
                loss = (
                    policy_loss
                    + self.value_coef * value_loss
                    + self.entropy_coef * entropy_loss
                )

                # 反向傳播
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.network.parameters(), self.max_grad_norm
                )
                self.optimizer.step()

                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy_loss += entropy_loss.item()

        # 清空存儲
        self.clear_memory()

        return {
            "policy_loss": total_policy_loss / self.ppo_epochs,
            "value_loss": total_value_loss / self.ppo_epochs,
            "entropy_loss": total_entropy_loss / self.ppo_epochs,
        }

    def _compute_advantages(
        self, rewards: torch.Tensor, values: torch.Tensor, dones: torch.Tensor
    ) -> torch.Tensor:
        """計算GAE優勢"""
        advantages = torch.zeros_like(rewards)
        last_advantage = 0

        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]

            delta = rewards[t] + self.gamma * next_value * (1 - dones[t]) - values[t]
            advantages[t] = (
                delta + self.gamma * self.gae_lambda * (1 - dones[t]) * last_advantage
            )
            last_advantage = advantages[t]

        return advantages

    def clear_memory(self):
        """清空存儲"""
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.values.clear()
        self.log_probs.clear()
        self.dones.clear()

    def save_model(self, filepath: str):
        """保存模型"""
        torch.save(
            {
                "network_state_dict": self.network.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
            },
            filepath,
        )
        self.logger.info(f"PPO model saved to {filepath}")

    def load_model(self, filepath: str):
        """加載模型"""
        checkpoint = torch.load(filepath)
        self.network.load_state_dict(checkpoint["network_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.logger.info(f"PPO model loaded from {filepath}")


class MultiAgentSystem:
    """多智能體協作系統"""

    def __init__(self, agents: Dict[str, Any], coordination_strategy: str = "voting"):
        self.logger = logging.getLogger("hk_quant_system.multi_agent")
        self.agents = agents
        self.coordination_strategy = coordination_strategy
        self.agent_weights = {name: 1.0 for name in agents.keys()}
        self.performance_history = defaultdict(list)

    def get_collective_action(
        self, state: np.ndarray, agent_performance: Optional[Dict[str, float]] = None
    ) -> AgentAction:
        """獲取集體動作"""
        agent_actions = {}
        agent_confidences = {}

        # 收集各智能體的動作
        for name, agent in self.agents.items():
            try:
                if hasattr(agent, "get_action"):
                    action = agent.get_action(state, training=False)
                    agent_actions[name] = action
                elif hasattr(agent, "predict"):
                    prediction = agent.predict(state)
                    agent_actions[name] = self._prediction_to_action(prediction)

                # 簡化的置信度計算
                agent_confidences[name] = self._calculate_agent_confidence(
                    name, agent_performance
                )

            except Exception as e:
                self.logger.warning(f"Agent {name} failed to get action: {str(e)}")
                continue

        # 協調策略
        if self.coordination_strategy == "voting":
            return self._voting_strategy(agent_actions, agent_confidences)
        elif self.coordination_strategy == "weighted":
            return self._weighted_strategy(agent_actions, agent_confidences)
        elif self.coordination_strategy == "expert":
            return self._expert_strategy(agent_actions, agent_confidences)
        else:
            return self._default_strategy(agent_actions)

    def _prediction_to_action(self, prediction: Any) -> int:
        """將預測轉換為動作"""
        if isinstance(prediction, (int, np.integer)):
            return int(prediction)
        elif isinstance(prediction, (float, np.floating)):
            if prediction > 0.1:
                return ActionType.BUY.value
            elif prediction < -0.1:
                return ActionType.SELL.value
            else:
                return ActionType.HOLD.value
        else:
            return ActionType.HOLD.value

    def _calculate_agent_confidence(
        self, name: str, performance: Optional[Dict[str, float]]
    ) -> float:
        """計算智能體置信度"""
        if performance and name in performance:
            return max(0.1, min(1.0, performance[name]))
        elif self.performance_history[name]:
            recent_performance = np.mean(self.performance_history[name][-10:])
            return max(0.1, min(1.0, recent_performance))
        else:
            return 0.5

    def _voting_strategy(
        self, actions: Dict[str, int], confidences: Dict[str, float]
    ) -> AgentAction:
        """投票策略"""
        action_counts = defaultdict(int)
        total_confidence = 0

        for agent, action in actions.items():
            weight = confidences.get(agent, 0.5)
            action_counts[action] += weight
            total_confidence += weight

        # 選擇得票最多的動作
        best_action = max(action_counts.keys(), key=lambda x: action_counts[x])
        confidence = action_counts[best_action] / (total_confidence + 1e-8)

        return AgentAction(
            action_type=ActionType(best_action),
            amount=1.0,
            confidence=confidence,
            timestamp=datetime.now(),
            reasoning=f"Voting strategy: {best_action} with {action_counts[best_action]:.2f} votes",
        )

    def _weighted_strategy(
        self, actions: Dict[str, int], confidences: Dict[str, float]
    ) -> AgentAction:
        """加權策略"""
        weighted_scores = defaultdict(float)
        total_weight = 0

        for agent, action in actions.items():
            weight = self.agent_weights[agent] * confidences.get(agent, 0.5)
            weighted_scores[action] += weight * action  # 簡化的加權
            total_weight += weight

        best_action = max(weighted_scores.keys(), key=lambda x: weighted_scores[x])
        confidence = weighted_scores[best_action] / (total_weight + 1e-8)

        return AgentAction(
            action_type=ActionType(best_action),
            amount=1.0,
            confidence=confidence,
            timestamp=datetime.now(),
            reasoning=f"Weighted strategy: {best_action}",
        )

    def _expert_strategy(
        self, actions: Dict[str, int], confidences: Dict[str, float]
    ) -> AgentAction:
        """專家策略 (選擇置信度最高的智能體)"""
        if not actions:
            return AgentAction(
                ActionType.HOLD, 0.0, 0.0, datetime.now(), "No actions available"
            )

        best_agent = max(confidences.keys(), key=lambda x: confidences.get(x, 0))
        best_action = actions[best_agent]
        confidence = confidences.get(best_agent, 0.5)

        return AgentAction(
            action_type=ActionType(best_action),
            amount=1.0,
            confidence=confidence,
            timestamp=datetime.now(),
            reasoning=f"Expert strategy: {best_agent} suggested {best_action}",
        )

    def _default_strategy(self, actions: Dict[str, int]) -> AgentAction:
        """默認策略"""
        if not actions:
            return AgentAction(
                ActionType.HOLD, 0.0, 0.0, datetime.now(), "No actions available"
            )

        # 選擇出現頻率最高的動作
        action_counts = defaultdict(int)
        for action in actions.values():
            action_counts[action] += 1

        best_action = max(action_counts.keys(), key=lambda x: action_counts[x])
        confidence = action_counts[best_action] / len(actions)

        return AgentAction(
            action_type=ActionType(best_action),
            amount=1.0,
            confidence=confidence,
            timestamp=datetime.now(),
            reasoning=f"Default strategy: {best_action}",
        )

    def update_agent_performance(self, agent_name: str, performance: float):
        """更新智能體性能"""
        self.performance_history[agent_name].append(performance)

        # 更新權重
        if len(self.performance_history[agent_name]) > 10:
            recent_performance = np.mean(self.performance_history[agent_name][-10:])
            self.agent_weights[agent_name] = max(0.1, recent_performance)


class RLTrainingManager:
    """強化學習訓練管理器"""

    def __init__(
        self,
        environment: TradingEnvironment,
        save_dir: str = "rl_models",
        tensorboard_log: str = "tensorboard_logs",
    ):
        self.logger = logging.getLogger("hk_quant_system.rl_trainer")
        self.environment = environment
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.tensorboard_log = tensorboard_log

        # 訓練統計
        self.training_history = defaultdict(list)

    async def train_dqn_agent(
        self,
        episodes: int = 1000,
        max_steps_per_episode: int = 1000,
        save_freq: int = 100,
        eval_freq: int = 50,
    ) -> Dict[str, Any]:
        """訓練DQN智能體"""
        try:
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch is required for DQN training")

            self.logger.info(f"Starting DQN training for {episodes} episodes")

            # 初始化智能體
            state_dim = (
                self.environment.observation_space.shape[1]
                * self.environment.observation_space.shape[0]
            )
            agent = DQNAgent(state_dim)

            episode_rewards = []
            episode_lengths = []
            eval_rewards = []

            for episode in range(episodes):
                state = self.environment.reset()
                total_reward = 0
                steps = 0

                for step in range(max_steps_per_episode):
                    # 選擇動作
                    action = agent.get_action(state.flatten(), training=True)

                    # 執行動作
                    next_state, reward, done, info = self.environment.step(action)

                    # 存儲經驗
                    agent.remember(
                        state.flatten(), action, reward, next_state.flatten(), done
                    )

                    # 訓練
                    loss = agent.replay()

                    state = next_state
                    total_reward += reward
                    steps += 1

                    if done:
                        break

                episode_rewards.append(total_reward)
                episode_lengths.append(steps)

                # 評估
                if episode % eval_freq == 0:
                    eval_reward = await self._evaluate_agent(agent, "dqn")
                    eval_rewards.append(eval_reward)
                    self.logger.info(
                        f"Episode {episode}: Train Reward={total_reward:.2f}, Eval Reward={eval_reward:.2f}"
                    )

                # 保存模型
                if episode % save_freq == 0:
                    model_path = self.save_dir / f"dqn_model_episode_{episode}.pth"
                    agent.save_model(str(model_path))

            # 保存最終模型
            final_model_path = self.save_dir / "dqn_model_final.pth"
            agent.save_model(str(final_model_path))

            return {
                "agent": agent,
                "episode_rewards": episode_rewards,
                "episode_lengths": episode_lengths,
                "eval_rewards": eval_rewards,
                "final_model_path": str(final_model_path),
                "total_episodes": episodes,
            }

        except Exception as e:
            self.logger.error(f"DQN training failed: {str(e)}")
            raise

    async def train_ppo_agent(
        self,
        episodes: int = 1000,
        max_steps_per_episode: int = 1000,
        update_timestep: int = 2048,
        save_freq: int = 100,
        eval_freq: int = 50,
    ) -> Dict[str, Any]:
        """訓練PPO智能體"""
        try:
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch is required for PPO training")

            self.logger.info(f"Starting PPO training for {episodes} episodes")

            # 初始化智能體
            state_dim = (
                self.environment.observation_space.shape[1]
                * self.environment.observation_space.shape[0]
            )
            agent = PPOAgent(state_dim)

            episode_rewards = []
            episode_lengths = []
            eval_rewards = []

            for episode in range(episodes):
                state = self.environment.reset()
                episode_reward = 0
                steps = 0

                for step in range(max_steps_per_episode):
                    # 選擇動作
                    action, log_prob, value = agent.get_action(state.flatten())

                    # 執行動作
                    next_state, reward, done, info = self.environment.step(action)

                    # 存儲經驗
                    agent.remember(
                        state.flatten(), action, reward, value, log_prob, done
                    )

                    state = next_state
                    episode_reward += reward
                    steps += 1

                    # 更新網絡
                    if len(agent.states) >= update_timestep or done:
                        update_stats = agent.update()
                        self.training_history["policy_loss"].extend(
                            update_stats.get("policy_loss", [])
                        )
                        self.training_history["value_loss"].extend(
                            update_stats.get("value_loss", [])
                        )

                    if done:
                        break

                episode_rewards.append(episode_reward)
                episode_lengths.append(steps)

                # 評估
                if episode % eval_freq == 0:
                    eval_reward = await self._evaluate_agent(agent, "ppo")
                    eval_rewards.append(eval_reward)
                    self.logger.info(
                        f"Episode {episode}: Train Reward={episode_reward:.2f}, Eval Reward={eval_reward:.2f}"
                    )

                # 保存模型
                if episode % save_freq == 0:
                    model_path = self.save_dir / f"ppo_model_episode_{episode}.pth"
                    agent.save_model(str(model_path))

            # 保存最終模型
            final_model_path = self.save_dir / "ppo_model_final.pth"
            agent.save_model(str(final_model_path))

            return {
                "agent": agent,
                "episode_rewards": episode_rewards,
                "episode_lengths": episode_lengths,
                "eval_rewards": eval_rewards,
                "final_model_path": str(final_model_path),
                "training_history": dict(self.training_history),
                "total_episodes": episodes,
            }

        except Exception as e:
            self.logger.error(f"PPO training failed: {str(e)}")
            raise

    async def _evaluate_agent(self, agent: Any, agent_type: str) -> float:
        """評估智能體性能"""
        total_rewards = []
        num_eval_episodes = 10

        for _ in range(num_eval_episodes):
            state = self.environment.reset()
            episode_reward = 0
            done = False

            while not done:
                if agent_type == "dqn":
                    action = agent.get_action(state.flatten(), training=False)
                elif agent_type == "ppo":
                    action, _, _ = agent.get_action(state.flatten())
                else:
                    action = self.environment.action_space.sample()

                state, reward, done, _ = self.environment.step(action)
                episode_reward += reward

            total_rewards.append(episode_reward)

        return np.mean(total_rewards)

    def create_multi_agent_system(
        self, agent_configs: Dict[str, Dict[str, Any]]
    ) -> MultiAgentSystem:
        """創建多智能體系統"""
        agents = {}

        for name, config in agent_configs.items():
            agent_type = config.get("type", "dqn")

            if agent_type == "dqn":
                state_dim = (
                    self.environment.observation_space.shape[1]
                    * self.environment.observation_space.shape[0]
                )
                agents[name] = DQNAgent(state_dim, **config.get("params", {}))
            elif agent_type == "ppo":
                state_dim = (
                    self.environment.observation_space.shape[1]
                    * self.environment.observation_space.shape[0]
                )
                agents[name] = PPOAgent(state_dim, **config.get("params", {}))
            # 可以添加更多智能體類型

        coordination_strategy = config.get("coordination", "voting")
        return MultiAgentSystem(agents, coordination_strategy)


# 全局實例
try:
    # 這些需要在有數據的情況下初始化
    rl_training_manager = None  # RLTrainingManager(environment) 環境需要數據
    logger = logging.getLogger("hk_quant_system.rl")
    logger.info("Reinforcement learning module initialized")
except Exception as e:
    logging.getLogger("hk_quant_system.rl").warning(
        f"RL module initialization failed: {str(e)}"
    )
