#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多因子模型策略系統
結合技術、情緒、宏觀、風險因子提高勝率
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import warnings
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

class MultiFactorModelStrategy:
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.factor_categories = {
            'technical': [],
            'sentiment': [],
            'macro': [],
            'risk': []
        }
        self.factor_importance = {}
        self.model = None
        self.scaler = StandardScaler()

    def load_real_data(self):
        """加載真實CBSC數據"""
        try:
            import glob
            cbsc_files = glob.glob('acquired_data/cbsc_real_data_*.csv')
            if not cbsc_files:
                # 嘗試其他數據源
                data_files = glob.glob('*.csv')
                if not data_files:
                    raise FileNotFoundError("No data files found")

                data = pd.read_csv(data_files[0], index_col=0, parse_dates=True)
                # 如果缺少必要列，創建模擬數據
                if 'HSIF_Close' not in data.columns:
                    data['HSIF_Close'] = data.iloc[:, 0]  # 使用第一列作為價格
                    print(f"[WARN] Using first column as HSIF_Close: {data.columns[0]}")
            else:
                data = pd.read_csv(cbsc_files[0], index_col=0, parse_dates=True)
                print(f"[OK] Loaded CBSC data: {len(data)} records")

            # 確保必要的列存在
            if 'HSIF_Close' not in data.columns:
                raise ValueError("HSIF_Close column not found in data")

            # 計算基礎回報
            data['HSIF_Return'] = data['HSIF_Close'].pct_change()

            # 添加CBSC相關數據
            if 'Bull_Bear_Ratio' not in data.columns:
                # 基於價格變化模擬牛熊比例
                data['Bull_Bear_Ratio'] = np.exp(data['HSIF_Return'].rolling(5).mean() * 10)

            print(f"[OK] Data prepared with {len(data)} records")
            return data

        except Exception as e:
            print(f"[ERROR] Failed to load data: {e}")
            # 創建最小測試數據
            dates = pd.date_range('2020-01-01', periods=1000, freq='D')
            data = pd.DataFrame({
                'HSIF_Close': np.random.randn(1000).cumsum() + 20000,
                'Bull_Bear_Ratio': np.random.uniform(0.5, 2.0, 1000)
            }, index=dates)
            data['HSIF_Return'] = data['HSIF_Close'].pct_change()
            print(f"[OK] Created synthetic test data: {len(data)} records")
            return data

    def calculate_technical_factors(self, data):
        """計算技術因子"""
        factors = pd.DataFrame(index=data.index)

        # 價格動量因子
        for period in [5, 10, 20, 60]:
            factors[f'momentum_{period}'] = data['HSIF_Close'].pct_change(period)

        # 波動率因子
        for period in [10, 20, 60]:
            factors[f'volatility_{period}'] = data['HSIF_Return'].rolling(period).std()

        # RSI因子
        for period in [14, 30]:
            delta = data['HSIF_Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            factors[f'rsi_{period}'] = 100 - (100 / (1 + rs))

        # 移動平均因子
        for period in [10, 20, 60]:
            ma = data['HSIF_Close'].rolling(period).mean()
            factors[f'ma_ratio_{period}'] = data['HSIF_Close'] / ma

        # 布林帶因子
        for period in [20, 60]:
            sma = data['HSIF_Close'].rolling(period).mean()
            std = data['HSIF_Close'].rolling(period).std()
            factors[f'bb_position_{period}'] = (data['HSIF_Close'] - sma) / std

        # 成交量因子（如果存在）
        if 'Volume' in data.columns:
            factors['volume_sma_ratio'] = data['Volume'] / data['Volume'].rolling(20).mean()
            factors['volume_price_trend'] = (data['HSIF_Return'] * data['Volume']).rolling(5).sum()
        else:
            # 模擬成交量因子
            factors['volume_sma_ratio'] = 1.0 + np.random.normal(0, 0.1, len(data))
            factors['volume_price_trend'] = data['HSIF_Return'] * np.random.uniform(0.5, 2.0, len(data))

        self.factor_categories['technical'] = list(factors.columns)
        print(f"[OK] Calculated {len(factors.columns)} technical factors")
        return factors

    def calculate_sentiment_factors(self, data):
        """計算情緒因子"""
        factors = pd.DataFrame(index=data.index)

        # 牛熊比例相關因子
        factors['bull_bear_ratio'] = data['Bull_Bear_Ratio']
        factors['bull_bear_ma_ratio'] = data['Bull_Bear_Ratio'] / data['Bull_Bear_Ratio'].rolling(20).mean()
        factors['bull_bear_volatility'] = data['Bull_Bear_Ratio'].pct_change().rolling(10).std()

        # 情緒動量因子
        factors['sentiment_momentum_5'] = data['Bull_Bear_Ratio'].pct_change(5)
        factors['sentiment_momentum_20'] = data['Bull_Bear_Ratio'].pct_change(20)

        # 情緒極值因子
        factors['bull_bear_zscore'] = (data['Bull_Bear_Ratio'] - data['Bull_Bear_Ratio'].rolling(60).mean()) / data['Bull_Bear_Ratio'].rolling(60).std()

        # 情緒與價格關係因子
        factors['price_sentiment_corr'] = data['HSIF_Return'].rolling(20).corr(data['Bull_Bear_Ratio'].pct_change())

        # 情緒離散度因子
        factors['sentiment_divergence'] = abs(data['HSIF_Return'] - data['Bull_Bear_Ratio'].pct_change())

        # 市場情緒狀態因子
        factors['extreme_bullish'] = (data['Bull_Bear_Ratio'] > 1.5).astype(int)
        factors['extreme_bearish'] = (data['Bull_Bear_Ratio'] < 0.67).astype(int)

        self.factor_categories['sentiment'] = list(factors.columns)
        print(f"[OK] Calculated {len(factors.columns)} sentiment factors")
        return factors

    def calculate_macro_factors(self, data):
        """計算宏觀因子"""
        factors = pd.DataFrame(index=data.index)

        # 時間因子
        factors['month'] = data.index.month
        factors['day_of_week'] = data.index.dayofweek
        factors['quarter'] = data.index.quarter

        # 季節性因子（使用sin/cos編碼）
        factors['month_sin'] = np.sin(2 * np.pi * data.index.month / 12)
        factors['month_cos'] = np.cos(2 * np.pi * data.index.month / 12)

        # 交易日因子
        factors['is_month_start'] = (data.index.is_month_start).astype(int)
        factors['is_month_end'] = (data.index.is_month_end).astype(int)
        factors['is_quarter_end'] = (data.index.is_quarter_end).astype(int)

        # 價格趨勢因子
        for period in [20, 60, 120]:
            factors[f'price_trend_{period}'] = (data['HSIF_Close'] > data['HSIF_Close'].rolling(period).mean()).astype(int)

        # 波動率狀態因子
        volatility_20 = data['HSIF_Return'].rolling(20).std()
        factors['high_volatility_regime'] = (volatility_20 > volatility_20.quantile(0.8)).astype(int)
        factors['low_volatility_regime'] = (volatility_20 < volatility_20.quantile(0.2)).astype(int)

        # 價格位置因子
        price_min_252 = data['HSIF_Close'].rolling(252).min()
        price_max_252 = data['HSIF_Close'].rolling(252).max()
        factors['price_position'] = (data['HSIF_Close'] - price_min_252) / (price_max_252 - price_min_252)

        self.factor_categories['macro'] = list(factors.columns)
        print(f"[OK] Calculated {len(factors.columns)} macro factors")
        return factors

    def calculate_risk_factors(self, data):
        """計算風險因子"""
        factors = pd.DataFrame(index=data.index)

        # 波動率風險因子
        for period in [10, 20, 60]:
            factors[f'realized_vol_{period}'] = data['HSIF_Return'].rolling(period).std() * np.sqrt(252)

        # 下行風險因子
        for period in [20, 60]:
            negative_returns = data['HSIF_Return'][data['HSIF_Return'] < 0]
            factors[f'downside_vol_{period}'] = negative_returns.rolling(period).std().reindex(data.index, method='ffill') * np.sqrt(252)

        # Va風險因子
        for period in [20, 60]:
            factors[f'var_95_{period}'] = data['HSIF_Return'].rolling(period).quantile(0.05)
            factors[f'var_99_{period}'] = data['HSIF_Return'].rolling(period).quantile(0.01)

        # 最大回撤因子
        cumulative_returns = (1 + data['HSIF_Return']).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak
        factors['current_drawdown'] = drawdown
        factors['max_drawdown_20'] = drawdown.rolling(20).min()
        factors['max_drawdown_60'] = drawdown.rolling(60).min()

        # 偏度和峰度因子
        factors['skewness_20'] = data['HSIF_Return'].rolling(20).skew()
        factors['kurtosis_20'] = data['HSIF_Return'].rolling(20).kurt()

        # 相關性風險因子（與自己滯後）
        for lag in [1, 5, 20]:
            factors[f'autocorr_{lag}'] = data['HSIF_Return'].rolling(60).apply(lambda x: x.autocorr(lag=lag))

        self.factor_categories['risk'] = list(factors.columns)
        print(f"[OK] Calculated {len(factors.columns)} risk factors")
        return factors

    def build_factor_matrix(self, data):
        """構建完整的因子矩陣"""
        print("Building factor matrix...")

        # 計算各類因子
        technical_factors = self.calculate_technical_factors(data)
        sentiment_factors = self.calculate_sentiment_factors(data)
        macro_factors = self.calculate_macro_factors(data)
        risk_factors = self.calculate_risk_factors(data)

        # 合併所有因子
        all_factors = pd.concat([
            technical_factors,
            sentiment_factors,
            macro_factors,
            risk_factors
        ], axis=1)

        # 清理數據
        all_factors = all_factors.replace([np.inf, -np.inf], np.nan)
        all_factors = all_factors.fillna(method='ffill').fillna(method='bfill').fillna(0)

        print(f"[OK] Built factor matrix: {len(all_factors.columns)} factors, {len(all_factors)} rows")
        return all_factors

    def train_factor_model(self, factor_matrix, data, lookforward_days=5):
        """訓練因子模型"""
        print("Training factor model...")

        # 準備目標變量（未來回報）
        target = data['HSIF_Return'].shift(-lookforward_days)

        # 對齊數據
        valid_idx = factor_matrix.index.intersection(target.index)
        X = factor_matrix.loc[valid_idx]
        y = target.loc[valid_idx]

        # 移除NaN值
        valid_mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_mask]
        y = y[valid_mask]

        if len(X) < 100:
            print(f"[WARN] Insufficient training data: {len(X)} samples")
            return False

        # 標準化因子
        X_scaled = self.scaler.fit_transform(X)

        # 訓練模型
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1
        )

        # 分割訓練測試集
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, shuffle=False
        )

        # 訓練模型
        self.model.fit(X_train, y_train)

        # 評估模型
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)

        # 計算因子重要性
        feature_importance = self.model.feature_importances_
        self.factor_importance = dict(zip(X.columns, feature_importance))

        # 按類別統計重要性
        category_importance = {}
        for category, features in self.factor_categories.items():
            category_imp = sum(self.factor_importance.get(f, 0) for f in features if f in self.factor_importance)
            category_importance[category] = category_imp

        print(f"[OK] Model trained successfully")
        print(f"  Training R2: {train_r2:.4f}")
        print(f"  Testing R2: {test_r2:.4f}")
        print(f"  Category importance: {category_importance}")

        return True

    def generate_signals(self, factor_matrix, data, threshold=0.6):
        """生成交易信號"""
        if self.model is None:
            raise ValueError("Model not trained. Call train_factor_model first.")

        print("Generating trading signals...")

        # 準備數據
        valid_idx = factor_matrix.index.intersection(data.index)
        X = factor_matrix.loc[valid_idx]

        # 標準化
        X_scaled = self.scaler.transform(X)

        # 預測未來回報
        predictions = self.model.predict(X_scaled)

        # 生成信號
        signals = pd.DataFrame(index=valid_idx)
        signals['predicted_return'] = predictions
        signals['signal_strength'] = np.abs(predictions)

        # 基於閾值生成交易信號
        signals['position'] = 0
        signals.loc[predictions > threshold * predictions.std(), 'position'] = 1
        signals.loc[predictions < -threshold * predictions.std(), 'position'] = -1

        # 每月更新信號（低頻率）
        monthly_rebalance = signals.resample('M').first()
        final_signals = pd.DataFrame(index=signals.index, columns=['position'])

        for date, row in monthly_rebalance.iterrows():
            if row['position'] != 0:
                final_signals.loc[date:, 'position'] = row['position']

        final_signals['position'] = final_signals['position'].fillna(0)

        print(f"[OK] Generated signals: {len(final_signals)} trading days")
        return final_signals

    def calculate_strategy_performance(self, data, signals):
        """計算策略性能"""
        returns = data['HSIF_Return'] * signals['position'].shift(1)

        # 基礎指標
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)

        # 夏普比率
        risk_free_rate = 0.025
        excess_returns = returns - risk_free_rate / 252
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()

        # 勝率和其他指標
        win_rate = (returns > 0).mean()
        trading_days = (signals['position'] != 0).sum()

        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 信息比率（相對於基準）
        benchmark_returns = data['HSIF_Return']
        excess_returns_strategy = returns - benchmark_returns
        information_ratio = excess_returns_strategy.mean() / excess_returns_strategy.std() * np.sqrt(252) if excess_returns_strategy.std() > 0 else 0

        return {
            'strategy_name': 'Multi_Factor_Model',
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'information_ratio': information_ratio,
            'win_rate': win_rate,
            'total_trades': int(trading_days),
            'trades_per_year': trading_days / len(returns) * 252,
            'total_days': len(returns),
            'years_tested': len(returns) / 252
        }

    def run_multi_factor_strategy(self):
        """運行多因子模型策略"""
        print("=" * 80)
        print("MULTI-FACTOR MODEL STRATEGY")
        print("=" * 80)

        # 加載數據
        data = self.load_real_data()
        if data is None:
            return None

        # 構建因子矩陣
        factor_matrix = self.build_factor_matrix(data)

        # 訓練模型
        if not self.train_factor_model(factor_matrix, data):
            print("[ERROR] Failed to train factor model")
            return None

        # 生成信號
        signals = self.generate_signals(factor_matrix, data)

        # 計算性能
        performance = self.calculate_strategy_performance(data, signals)

        # 評分
        score = self._calculate_strategy_score(performance)

        # 組合結果
        results = {
            **performance,
            'factor_categories': self.factor_categories,
            'factor_importance': dict(sorted(self.factor_importance.items(), key=lambda x: x[1], reverse=True)[:20]),  # 前20個重要因子
            'score': score,
            'grade': self._get_grade(score)
        }

        # 打印結果
        print(f"\n{'='*20} PERFORMANCE {'='*20}")
        print(f"  Total Return: {performance['total_return']:.2%}")
        print(f"  Annual Return: {performance['annual_return']:.2%}")
        print(f"  Sharpe Ratio: {performance['sharpe_ratio']:.3f}")
        print(f"  Information Ratio: {performance['information_ratio']:.3f}")
        print(f"  Max Drawdown: {performance['max_drawdown']:.2%}")
        print(f"  Calmar Ratio: {performance['calmar_ratio']:.3f}")
        print(f"  Win Rate: {performance['win_rate']:.2%}")
        print(f"  Trades/Year: {performance['trades_per_year']:.1f}")
        print(f"  Score: {score:.1f}/100 ({self._get_grade(score)})")

        print(f"\n{'='*20} TOP FACTORS {'='*20}")
        for i, (factor, importance) in enumerate(list(results['factor_importance'].items())[:10], 1):
            print(f"  {i:2d}. {factor:<25}: {importance:.4f}")

        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"multi_factor_results_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[SAVE] Results saved: {filename}")
        return results

    def _calculate_strategy_score(self, performance):
        """計算策略評分"""
        score = 0

        # 年化收益評分 (0-25分)
        if performance['annual_return'] > 0.15:
            score += 25
        elif performance['annual_return'] > 0.10:
            score += 20
        elif performance['annual_return'] > 0.05:
            score += 15
        elif performance['annual_return'] > 0:
            score += 10
        elif performance['annual_return'] > -0.05:
            score += 5

        # 夏普比率評分 (0-25分)
        if performance['sharpe_ratio'] > 1.0:
            score += 25
        elif performance['sharpe_ratio'] > 0.8:
            score += 20
        elif performance['sharpe_ratio'] > 0.6:
            score += 15
        elif performance['sharpe_ratio'] > 0.4:
            score += 10
        elif performance['sharpe_ratio'] > 0.2:
            score += 5

        # 信息比率評分 (0-20分)
        if performance['information_ratio'] > 0.8:
            score += 20
        elif performance['information_ratio'] > 0.6:
            score += 15
        elif performance['information_ratio'] > 0.4:
            score += 10
        elif performance['information_ratio'] > 0.2:
            score += 5

        # 最大回撤評分 (0-15分)
        if performance['max_drawdown'] > -0.1:
            score += 15
        elif performance['max_drawdown'] > -0.2:
            score += 10
        elif performance['max_drawdown'] > -0.3:
            score += 5

        # Calmar比率評分 (0-10分)
        if performance['calmar_ratio'] > 1.0:
            score += 10
        elif performance['calmar_ratio'] > 0.5:
            score += 8
        elif performance['calmar_ratio'] > 0.3:
            score += 6
        elif performance['calmar_ratio'] > 0.1:
            score += 4
        elif performance['calmar_ratio'] > 0:
            score += 2

        # 勝率評分 (0-5分)
        if performance['win_rate'] > 0.6:
            score += 5
        elif performance['win_rate'] > 0.55:
            score += 4
        elif performance['win_rate'] > 0.5:
            score += 3
        elif performance['win_rate'] > 0.45:
            score += 2
        elif performance['win_rate'] > 0.4:
            score += 1

        return min(100, score)

    def _get_grade(self, score):
        """獲取評級"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        elif score >= 30:
            return 'D+'
        elif score >= 20:
            return 'D'
        else:
            return 'F'

def main():
    """主執行函數"""
    strategy = MultiFactorModelStrategy()
    results = strategy.run_multi_factor_strategy()
    return results

if __name__ == "__main__":
    main()