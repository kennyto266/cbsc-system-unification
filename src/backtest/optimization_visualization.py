"""
Optimization Visualization Module
==================================

Visualization tools for parameter optimization results.
Creates plots for convergence curves, parameter distributions, and method comparisons.

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available, falling back to matplotlib")

try:
    import seaborn as sns
    sns.set_style("whitegrid")
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    logger.warning("Seaborn not available")


@dataclass
class VisualizationConfig:
    """Configuration for optimization visualization"""
    figsize: tuple = (12, 8)
    dpi: int = 100
    style: str = 'seaborn-v0_8-whitegrid'
    color_palette: str = 'viridis'
    font_size: int = 10
    title_font_size: int = 14
    save_format: str = 'png'  # 'png', 'svg', 'pdf'


class OptimizationVisualizer:
    """
    Visualizer for parameter optimization results.

    Creates various plots to analyze optimization performance:
    - Convergence curves
    - Parameter distributions
    - Method comparison
    - Parameter importance
    - 2D/3D parameter space exploration
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """
        Initialize visualizer

        Args:
            config: Visualization configuration
        """
        self.config = config or VisualizationConfig()
        self._setup_style()

    def _setup_style(self):
        """Setup matplotlib style"""
        plt.style.use(self.config.style if hasattr(plt.style, self.config.style) else 'default')
        plt.rcParams['figure.figsize'] = self.config.figsize
        plt.rcParams['figure.dpi'] = self.config.dpi
        plt.rcParams['font.size'] = self.config.font_size
        plt.rcParams['axes.titlesize'] = self.config.title_font_size
        plt.rcParams['axes.labelsize'] = self.config.font_size + 1

    @staticmethod
    def _ensure_dict(result: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        """
        Convert OptimizationResult dataclass to dict if needed.

        Args:
            result: Either a dict or an OptimizationResult dataclass

        Returns:
            Dictionary representation
        """
        if isinstance(result, dict):
            return result
        # Handle OptimizationResult dataclass
        if hasattr(result, '__dataclass_fields__'):
            return {
                'best_params': getattr(result, 'best_params', {}),
                'best_score': getattr(result, 'best_score', 0),
                'best_iteration': getattr(result, 'best_iteration', 0),
                'convergence_curve': getattr(result, 'convergence_curve', []),
                'optimization_history': getattr(result, 'optimization_history', []),
                'n_evaluations': getattr(result, 'n_evaluations', 0),
                'runtime': getattr(result, 'runtime', 0),
            }
        # Fallback: try to convert to dict
        return dict(result) if hasattr(result, '__dict__') else result

    def plot_convergence(
        self,
        results: List[Dict[str, Any]],
        method_names: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot convergence curves for optimization methods.

        Args:
            results: List of optimization results (each with convergence_curve)
            method_names: Names of optimization methods
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)

        for i, result in enumerate(results):
            result_dict = self._ensure_dict(result)
            convergence = result_dict.get('convergence_curve', [])
            if convergence:
                name = method_names[i] if method_names and i < len(method_names) else f"Method {i+1}"
                ax.plot(convergence, label=name, linewidth=2, alpha=0.8)

        ax.set_xlabel('Iteration', fontsize=self.config.font_size + 1)
        ax.set_ylabel('Objective Value', fontsize=self.config.font_size + 1)
        ax.set_title('Optimization Convergence Curves', fontsize=self.config.title_font_size)
        ax.legend(loc='best', fontsize=self.config.font_size)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, format=self.config.save_format, dpi=self.config.dpi, bbox_inches='tight')
            logger.info(f"Convergence plot saved to {save_path}")

        return fig

    def plot_parameter_distributions(
        self,
        optimization_history: List[Dict[str, Any]],
        param_names: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot parameter value distributions across optimization iterations.

        Args:
            optimization_history: History of parameter evaluations
            param_names: Names of parameters
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        # Extract parameter values
        param_data = {}
        for record in optimization_history:
            params = record.get('params', {})
            for name, value in params.items():
                if name not in param_data:
                    param_data[name] = []
                param_data[name].append(value)

        # Create subplots
        n_params = len(param_data)
        n_cols = min(3, n_params)
        n_rows = (n_params + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4))
        if n_params == 1:
            axes = np.array([axes])
        axes = axes.flatten()

        for i, (param_name, values) in enumerate(param_data.items()):
            ax = axes[i]
            ax.hist(values, bins=30, alpha=0.7, edgecolor='black')
            ax.set_xlabel(param_name, fontsize=self.config.font_size)
            ax.set_ylabel('Frequency', fontsize=self.config.font_size)
            ax.set_title(f'{param_name} Distribution', fontsize=self.config.font_size + 1)
            ax.grid(True, alpha=0.3)

        # Hide unused subplots
        for i in range(n_params, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, format=self.config.save_format, dpi=self.config.dpi, bbox_inches='tight')
            logger.info(f"Parameter distributions plot saved to {save_path}")

        return fig

    def plot_method_comparison(
        self,
        results: Dict[str, Dict[str, Any]],
        metrics: List[str] = ['best_score', 'n_evaluations', 'runtime'],
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Compare optimization methods across multiple metrics.

        Args:
            results: Dictionary of method_name -> result
            metrics: Metrics to compare
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        n_metrics = len(metrics)
        fig, axes = plt.subplots(1, n_metrics, figsize=(n_metrics * 5, 4))

        if n_metrics == 1:
            axes = [axes]

        method_names = list(results.keys())

        for i, metric in enumerate(metrics):
            ax = axes[i]
            values = [self._ensure_dict(results[m]).get(metric, 0) for m in method_names]

            # Use bar plot for categorical comparison
            colors = plt.cm.viridis(np.linspace(0, 1, len(method_names)))
            bars = ax.bar(method_names, values, color=colors, alpha=0.8, edgecolor='black')

            ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=self.config.font_size + 1)
            ax.set_title(f'{metric.replace("_", " ").title()} by Method', fontsize=self.config.font_size + 1)
            ax.tick_params(axis='x', rotation=45, labelsize=self.config.font_size)
            ax.tick_params(axis='y', labelsize=self.config.font_size)
            ax.grid(True, alpha=0.3, axis='y')

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                       f'{height:.2f}', ha='center', va='bottom', fontsize=self.config.font_size - 1)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, format=self.config.save_format, dpi=self.config.dpi, bbox_inches='tight')
            logger.info(f"Method comparison plot saved to {save_path}")

        return fig

    def plot_parameter_importance(
        self,
        optimization_history: List[Dict[str, Any]],
        score_key: str = 'score',
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Analyze and visualize parameter importance based on optimization results.

        Args:
            optimization_history: History of parameter evaluations
            score_key: Key for score values
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        # Extract data
        params_df = pd.DataFrame([r.get('params', {}) for r in optimization_history])
        scores = pd.Series([r.get(score_key, 0) for r in optimization_history])

        # Calculate importance using correlation
        importance = {}
        for col in params_df.columns:
            if params_df[col].dtype in [np.float64, np.int64]:
                importance[col] = abs(params_df[col].corr(scores))

        # Sort by importance
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))

        if sorted_importance:
            names, values = zip(*sorted_importance)
            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(names)))
            bars = ax.barh(range(len(names)), values, color=colors, edgecolor='black')
            ax.set_yticks(range(len(names)))
            ax.set_yticklabels(names, fontsize=self.config.font_size)
            ax.set_xlabel('Absolute Correlation with Score', fontsize=self.config.font_size + 1)
            ax.set_title('Parameter Importance', fontsize=self.config.title_font_size)
            ax.grid(True, alpha=0.3, axis='x')

            # Add value labels
            for i, (bar, val) in enumerate(zip(bars, values)):
                ax.text(val, i, f' {val:.3f}', va='center', fontsize=self.config.font_size - 1)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, format=self.config.save_format, dpi=self.config.dpi, bbox_inches='tight')
            logger.info(f"Parameter importance plot saved to {save_path}")

        return fig

    def plot_2d_parameter_space(
        self,
        optimization_history: List[Dict[str, Any]],
        param1: str,
        param2: str,
        score_key: str = 'score',
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Visualize 2D parameter space with score heatmap.

        Args:
            optimization_history: History of parameter evaluations
            param1: First parameter name
            param2: Second parameter name
            score_key: Key for score values
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        # Extract data
        params_df = pd.DataFrame([r.get('params', {}) for r in optimization_history])
        scores = pd.Series([r.get(score_key, 0) for r in optimization_history])

        # Filter data
        mask = (params_df[param1].notna()) & (params_df[param2].notna())
        x = params_df.loc[mask, param1].values
        y = params_df.loc[mask, param2].values
        z = scores.loc[mask].values

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))

        # Scatter plot with color mapping
        scatter = ax.scatter(x, y, c=z, cmap='viridis', s=100, alpha=0.7, edgecolors='black')
        ax.set_xlabel(param1, fontsize=self.config.font_size + 1)
        ax.set_ylabel(param2, fontsize=self.config.font_size + 1)
        ax.set_title(f'Parameter Space: {param1} vs {param2}', fontsize=self.config.title_font_size)

        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Score', fontsize=self.config.font_size + 1)

        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, format=self.config.save_format, dpi=self.config.dpi, bbox_inches='tight')
            logger.info(f"2D parameter space plot saved to {save_path}")

        return fig

    def plot_optimization_summary(
        self,
        result: Dict[str, Any],
        method_name: str = "Optimization",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create a comprehensive summary plot for a single optimization result.

        Args:
            result: Optimization result dictionary
            method_name: Name of optimization method
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig = plt.figure(figsize=(15, 10))
        gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

        # Ensure result is a dict
        result_dict = self._ensure_dict(result)

        # Extract convergence curve
        convergence = result_dict.get('convergence_curve', [])
        best_score = result_dict.get('best_score', 0)
        best_params = result_dict.get('best_params', {})

        # 1. Convergence curve (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        if convergence:
            ax1.plot(convergence, linewidth=2, color='steelblue')
            ax1.axhline(y=best_score, color='red', linestyle='--', label=f'Best: {best_score:.4f}')
            ax1.set_xlabel('Iteration')
            ax1.set_ylabel('Objective Value')
            ax1.set_title('Convergence Curve')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

        # 2. Score distribution (top right)
        ax2 = fig.add_subplot(gs[0, 1])
        if convergence:
            ax2.hist(convergence, bins=30, color='lightcoral', edgecolor='black', alpha=0.7)
            ax2.axvline(x=best_score, color='red', linestyle='--', linewidth=2)
            ax2.set_xlabel('Objective Value')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Score Distribution')
            ax2.grid(True, alpha=0.3, axis='y')

        # 3. Best parameters (bottom left)
        ax3 = fig.add_subplot(gs[1, :])
        ax3.axis('off')

        summary_text = f"Optimization Summary: {method_name}\n"
        summary_text += f"=" * 50 + "\n"
        summary_text += f"Best Score: {best_score:.6f}\n"
        summary_text += f"Evaluations: {result_dict.get('n_evaluations', 0)}\n"
        summary_text += f"Runtime: {result_dict.get('runtime', 0):.2f} seconds\n\n"
        summary_text += "Best Parameters:\n"
        for param, value in best_params.items():
            if isinstance(value, float):
                summary_text += f"  {param}: {value:.6f}\n"
            else:
                summary_text += f"  {param}: {value}\n"

        ax3.text(0.1, 0.9, summary_text, transform=ax3.transAxes,
                fontsize=12, verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        fig.suptitle(f'{method_name} Results', fontsize=self.config.title_font_size + 2, y=0.98)

        if save_path:
            fig.savefig(save_path, format=self.config.save_format, dpi=self.config.dpi, bbox_inches='tight')
            logger.info(f"Optimization summary plot saved to {save_path}")

        return fig

    def create_interactive_dashboard(
        self,
        results: Dict[str, Dict[str, Any]],
        save_path: Optional[str] = None
    ) -> Optional[go.Figure]:
        """
        Create interactive Plotly dashboard for optimization results.

        Args:
            results: Dictionary of method_name -> result
            save_path: Path to save HTML file

        Returns:
            Plotly Figure (if Plotly available)
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available, skipping interactive dashboard")
            return None

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Convergence Curves', 'Method Comparison',
                          'Best Scores', 'Evaluations vs Runtime'),
            specs=[[{'type': 'scatter'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'scatter'}]]
        )

        method_names = list(results.keys())

        # 1. Convergence curves
        for i, (method, result) in enumerate(results.items()):
            convergence = result.get('convergence_curve', [])
            if convergence:
                fig.add_trace(
                    go.Scatter(y=convergence, mode='lines', name=method,
                              showlegend=i < 5),  # Only show legend for first 5
                    row=1, col=1
                )

        # 2. Best scores comparison
        best_scores = [results[m].get('best_score', 0) for m in method_names]
        fig.add_trace(
            go.Bar(x=method_names, y=best_scores, name='Best Score',
                   marker_color='steelblue'),
            row=1, col=2
        )

        # 3. Evaluations comparison
        evaluations = [results[m].get('n_evaluations', 0) for m in method_names]
        fig.add_trace(
            go.Bar(x=method_names, y=evaluations, name='Evaluations',
                   marker_color='lightcoral'),
            row=2, col=1
        )

        # 4. Runtime vs Evaluations scatter
        runtimes = [results[m].get('runtime', 0) for m in method_names]
        fig.add_trace(
            go.Scatter(x=evaluations, y=runtimes, mode='markers+text',
                      text=method_names, textposition='top center',
                      marker=dict(size=10, color='lightgreen'),
                      name='Methods'),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title='Parameter Optimization Dashboard',
            height=800,
            showlegend=True
        )

        fig.update_xaxes(title_text="Iteration", row=1, col=1)
        fig.update_yaxes(title_text="Objective Value", row=1, col=1)
        fig.update_xaxes(title_text="Method", row=1, col=2)
        fig.update_yaxes(title_text="Best Score", row=1, col=2)
        fig.update_xaxes(title_text="Method", row=2, col=1)
        fig.update_yaxes(title_text="Evaluations", row=2, col=1)
        fig.update_xaxes(title_text="Evaluations", row=2, col=2)
        fig.update_yaxes(title_text="Runtime (s)", row=2, col=2)

        if save_path:
            fig.write_html(save_path)
            logger.info(f"Interactive dashboard saved to {save_path}")

        return fig


# Convenience functions
def visualize_optimization_results(
    results: Dict[str, Dict[str, Any]],
    output_dir: str = "./optimization_plots",
    config: Optional[VisualizationConfig] = None
) -> None:
    """
    Create all visualization plots for optimization results.

    Args:
        results: Dictionary of optimization results
        output_dir: Directory to save plots
        config: Visualization configuration
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    visualizer = OptimizationVisualizer(config)

    # Method comparison
    fig = visualizer.plot_method_comparison(
        results,
        save_path=os.path.join(output_dir, "method_comparison.png")
    )
    plt.close(fig)

    # Individual summaries
    for method, result in results.items():
        fig = visualizer.plot_optimization_summary(
            result,
            method_name=method,
            save_path=os.path.join(output_dir, f"{method}_summary.png")
        )
        plt.close(fig)

    # Interactive dashboard
    dashboard = visualizer.create_interactive_dashboard(
        results,
        save_path=os.path.join(output_dir, "interactive_dashboard.html")
    )

    logger.info(f"All visualizations saved to {output_dir}")


__all__ = [
    'OptimizationVisualizer',
    'VisualizationConfig',
    'visualize_optimization_results'
]
