#!/usr / bin / env python3
"""
Data Authenticity Verification System
数据真实性验证系统

A comprehensive multi - layer data authenticity verification system for quantitative trading
专为量化交易设计的综合多层真实性验证系统
"""

__version__ = "1.0.0"
__author__ = "Claude Code Assistant"

from .config.config_manager import ConfigManager
from .core.authenticator import BaseAuthenticator
from .interfaces.data_authenticity_manager import DataAuthenticityManager

__all__ = ["DataAuthenticityManager", "BaseAuthenticator", "ConfigManager"]
