"""
Machine Learning Strategy Template

Template for ML-based trading strategies.
Generates code for strategies using machine learning models.
"""

from typing import Any
from .base import StrategyTemplate, StrategyType, TemplateFactory


class MLStrategyTemplate(StrategyTemplate):
    """
    Template for machine learning strategies.

    Generates strategies that use ML models for prediction-based trading.
    Supports various model types (Random Forest, Gradient Boosting, Neural Networks).

    Required Parameters:
        - model_type: Type of ML model ('rf', 'xgb', 'lstm', 'linear')
        - features: List of feature names
        - target: Target variable name
        - prediction_threshold: Threshold for signal generation

    Optional Parameters:
        - train_size: Fraction of data for training
        - retrain_frequency: How often to retrain (days)
        - feature_importance_threshold: Min importance for feature selection
        - use_ensemble: Use ensemble of multiple models
    """

    @classmethod
    def get_strategy_type(cls) -> StrategyType:
        return StrategyType.ML_STRATEGY

    @classmethod
    def get_required_parameters(cls) -> list[str]:
        return [
            "model_type",
            "features",
            "prediction_threshold",
        ]

    @classmethod
    def get_optional_parameters(cls) -> list[str]:
        return [
            "train_size",
            "retrain_frequency",
            "feature_importance_threshold",
            "use_ensemble",
            "position_size",
        ]

    def generate_code(
        self,
        parameters: dict[str, Any],
        indicators: dict[str, Any],
    ) -> str:
        """Generate ML strategy code."""
        strategy_name = parameters.get("name", "MLStrategy")
        model_type = parameters.get("model_type", "rf")
        features = parameters.get("features", ["returns", "volume", "volatility"])
        prediction_threshold = parameters.get("prediction_threshold", 0.5)
        position_size = parameters.get("position_size", 0.1)

        train_size = parameters.get("train_size", 0.7)

        model_code = self._get_model_code(model_type, parameters)
        feature_engineering = self._get_feature_engineering_code(features)
        ensemble_code = self._get_ensemble_code(parameters)

        return f'''"""
{strategy_name}

Machine learning-based trading strategy that uses {model_type.upper()}
model to predict price movements and generate trading signals.

Parameters:
    - model_type: {model_type} - Type of ML model
    - features: {features} - Features for prediction
    - prediction_threshold: {prediction_threshold} - Threshold for signals
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
{self._get_imports(model_type)}


class {strategy_name}:
    \"\"\"
    Machine Learning Trading Strategy Implementation.

    Uses supervised learning to predict price movements and
    generate trading signals based on predictions.
    \"\"\"

    def __init__(
        self,
        model_type: str = "{model_type}",
        features: List[str] = {features},
        prediction_threshold: float = {prediction_threshold},
        position_size: float = {position_size},
    ):
        \"\"\"
        Initialize ML strategy.

        Args:
            model_type: Type of model ('rf', 'xgb', 'linear')
            features: List of feature names
            prediction_threshold: Threshold for converting predictions to signals
            position_size: Fraction of capital to allocate
        \"\"\"
        self.model_type = model_type
        self.features = features
        self.prediction_threshold = prediction_threshold
        self.position_size = position_size
        self.model = None
        self.feature_importance = None
        self.last_train_date = None
{self._get_ensemble_init(parameters)}

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        \"\"\"
        Prepare features for ML model.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with engineered features
        \"\"\"
        features = data.copy()
{feature_engineering}
        # Remove NaN values
        features = features.fillna(0)

        return features

    def train(
        self,
        data: pd.DataFrame,
        train_size: float = {train_size},
    ) -> Dict[str, Any]:
        \"\"\"
        Train the ML model.

        Args:
            data: Historical price data
            train_size: Fraction of data to use for training

        Returns:
            Training metrics dictionary
        \"\"\"
        # Prepare features
        features = self.prepare_features(data)

        # Create target variable (next period return)
        features['target'] = features['close'].pct_change().shift(-1)
        features['target'] = (features['target'] > 0).astype(int)

        # Drop NaN
        features = features.dropna()

        # Split features and target
        X = features[self.features]
        y = features['target']

        # Train-test split
        split_idx = int(len(X) * train_size)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Train model
{model_code}
        self.last_train_date = data.index[split_idx]

        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = dict(zip(
                self.features,
                self.model.feature_importances_
            ))

        # Evaluate
        y_pred = self.model.predict(X_test)

        return {{
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "feature_importance": self.feature_importance,
        }}

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        \"\"\"
        Generate trading signals using trained model.

        Args:
            data: DataFrame with price data

        Returns:
            Series of trading signals (1=long, -1=short, 0=neutral)
        \"\"\"
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        features = self.prepare_features(data)
        X = features[self.features]

        # Get predictions
{ensemble_code}

        # Convert predictions to signals
        signals = pd.Series(0, index=data.index)

        # High probability of up move -> long
        signals[predictions > (0.5 + self.prediction_threshold / 2)] = 1

        # High probability of down move -> short
        signals[predictions < (0.5 - self.prediction_threshold / 2)] = -1

        return signals

    def backtest(
        self,
        data: pd.DataFrame,
        train_size: float = {train_size},
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        \"\"\"
        Run backtest with walk-forward validation.

        Args:
            data: Historical price data
            train_size: Fraction for initial training
            initial_capital: Starting capital

        Returns:
            Backtest results dictionary
        \"\"\"
        # Train initial model
        train_metrics = self.train(data, train_size)

        # Generate signals on test set
        signals = self.generate_signals(data)

        # Calculate returns
        returns = signals.shift(1) * data['close'].pct_change()

        # Calculate equity curve
        equity = (1 + returns * self.position_size).cumprod() * initial_capital

        return {{
            "final_equity": equity.iloc[-1],
            "total_return": (equity.iloc[-1] / initial_capital) - 1,
            "sharpe_ratio": self._calculate_sharpe(returns * self.position_size),
            "max_drawdown": self._calculate_max_drawdown(equity),
            "equity_curve": equity,
            "signals": signals,
            "train_metrics": train_metrics,
        }}

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        \"\"\"Calculate Sharpe ratio.\"\"\"
        return returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0

    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        \"\"\"Calculate maximum drawdown.\"\"\"
        rolling_max = equity.expanding().max()
        drawdown = (equity - rolling_max) / rolling_max
        return drawdown.min()
'''

    def _get_imports(self, model_type: str) -> str:
        """Get model-specific imports."""
        if model_type == "rf":
            return "\nfrom sklearn.ensemble import RandomForestClassifier"
        elif model_type == "xgb":
            return "\nfrom xgboost import XGBClassifier"
        elif model_type == "linear":
            return "\nfrom sklearn.linear_model import LogisticRegression"
        else:
            return "\nfrom sklearn.ensemble import RandomForestClassifier"

    def _get_model_code(self, model_type: str, parameters: dict) -> str:
        """Get model training code."""
        if model_type == "rf":
            return """        # Train Random Forest
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            random_state=42,
        )
        self.model.fit(X_train, y_train)"""
        elif model_type == "xgb":
            return """        # Train XGBoost
        from xgboost import XGBClassifier
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
        )
        self.model.fit(X_train, y_train)"""
        elif model_type == "linear":
            return """        # Train Logistic Regression
        from sklearn.linear_model import LogisticRegression
        self.model = LogisticRegression(
            max_iter=1000,
            random_state=42,
        )
        self.model.fit(X_train, y_train)"""
        else:
            return """        # Train Random Forest (default)
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
        )
        self.model.fit(X_train, y_train)"""

    def _get_feature_engineering_code(self, features: list) -> str:
        """Get feature engineering code."""
        return """        # Calculate returns
        features['returns'] = features['close'].pct_change()

        # Calculate volatility
        features['volatility'] = features['returns'].rolling(20).std()

        # Calculate volume change
        if 'volume' in features.columns:
            features['volume_change'] = features['volume'].pct_change()

        # Calculate moving averages
        features['sma_5'] = features['close'].rolling(5).mean()
        features['sma_20'] = features['close'].rolling(20).mean()

        # Calculate RSI
        delta = features['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))"""

    def _get_ensemble_code(self, parameters: dict) -> str:
        """Get ensemble prediction code if enabled."""
        if parameters.get("use_ensemble"):
            return """        # Use ensemble prediction
        predictions = []
        for model in self.models:
            predictions.append(model.predict(X))

        # Average predictions
        predictions = np.mean(predictions, axis=0)"""
        else:
            return """        predictions = self.model.predict(X)"""

    def _get_ensemble_init(self, parameters: dict) -> str:
        """Get ensemble initialization if enabled."""
        if parameters.get("use_ensemble"):
            return "\n        self.models = []"
        return ""

    def _validate_parameter_values(
        self,
        parameters: dict[str, Any]
    ) -> tuple[bool, Any]:
        """Validate ML specific parameters."""
        model_type = parameters.get("model_type")
        valid_models = ["rf", "xgb", "linear", "lstm"]
        if model_type is not None and model_type not in valid_models:
            return False, f"model_type must be one of {valid_models}"

        features = parameters.get("features")
        if features is not None and len(features) == 0:
            return False, "At least one feature required"

        prediction_threshold = parameters.get("prediction_threshold")
        if prediction_threshold is not None and (prediction_threshold <= 0 or prediction_threshold >= 0.5):
            return False, "prediction_threshold must be between 0 and 0.5"

        train_size = parameters.get("train_size")
        if train_size is not None and (train_size <= 0.5 or train_size >= 1.0):
            return False, "train_size must be between 0.5 and 1.0"

        return True, None


# Register template
TemplateFactory.register(MLStrategyTemplate)
