# tui/utils/config.py
import os
import json
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

class Config:
    """配置管理"""

    DEFAULT_CONFIG = {
        "api_url": "http://localhost:3004",
        "ws_url": "ws://localhost:3004/ws",
        "theme": "dark",
        "auto_refresh": True,
        "refresh_interval": 5,
        "log_level": "INFO",
        "max_log_lines": 1000
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", ".config.json")

        self.config_path = Path(config_path).resolve()
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """加載配置"""
        load_dotenv()

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            except Exception as e:
                print(f"加載配置失敗: {e}")

        # 環境變量優先
        if os.getenv("CBSC_API_URL"):
            self.config["api_url"] = os.getenv("CBSC_API_URL")
        if os.getenv("CBSC_WS_URL"):
            self.config["ws_url"] = os.getenv("CBSC_WS_URL")

    def save(self):
        """保存配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失敗: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """設置配置值"""
        self.config[key] = value
        return self.save()

    def get_all(self) -> Dict[str, Any]:
        """獲取所有配置"""
        return self.config.copy()

    def reset(self):
        """重置為默認配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        return self.save()
