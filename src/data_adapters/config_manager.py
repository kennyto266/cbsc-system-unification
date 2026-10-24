"""
数据适配器配置管理器

管理多个数据适配器的配置，支持动态配置更新和验证。
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field, validator

from .base_adapter import DataAdapterConfig, DataSourceType
from .raw_data_adapter import RawDataAdapterConfig


class AdapterConfigEntry(BaseModel):
    """适配器配置条目"""
    name: str = Field(..., description="适配器名称")
    enabled: bool = Field(True, description="是否启用")
    priority: int = Field(1, ge=1, le=10, description="优先级（1-10，数字越小优先级越高）")
    # 使用 dict 以保留各适配器自定义字段
    config: Dict[str, Any] = Field(..., description="适配器配置原始字典")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('适配器名称不能为空')
        return v.strip()


class DataAdapterConfigManager:
    """数据适配器配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger("hk_quant_system.data_adapter.config_manager")
        self.config_file = config_file or "config/data_adapters.json"
        self.adapters: Dict[str, AdapterConfigEntry] = {}
        self._load_default_configs()
    
    def _load_default_configs(self) -> None:
        """加载默认配置"""
        # 黑人RAW DATA默认配置
        raw_data_config = RawDataAdapterConfig(
            source_path="C:\\Users\\Penguin8n\\Desktop\\黑人RAW DATA",
            data_directory="C:\\Users\\Penguin8n\\Desktop\\黑人RAW DATA",
            file_pattern="*.csv",
            encoding="utf-8",
            delimiter=",",
            date_column="date",
            symbol_column="symbol",
            price_columns={
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume"
            },
            market_cap_column="market_cap",
            pe_ratio_column="pe_ratio",
            update_frequency=60,
            max_retries=3,
            timeout=30,
            cache_enabled=True,
            cache_ttl=300,
            quality_threshold=0.8
        )
        
        self.adapters["raw_data"] = AdapterConfigEntry(
            name="raw_data",
            enabled=True,
            priority=1,
            config=raw_data_config.dict()
        )
        
        self.logger.info("Loaded default adapter configurations")
    
    async def load_config_from_file(self) -> bool:
        """从文件加载配置"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                self.logger.warning(f"Config file not found: {config_path}, using default configs")
                return True
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.adapters.clear()
            
            for adapter_data in config_data.get('adapters', []):
                adapter_entry = AdapterConfigEntry(**adapter_data)
                self.adapters[adapter_entry.name] = adapter_entry
            
            self.logger.info(f"Loaded {len(self.adapters)} adapter configurations from {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load config from file: {e}")
            return False
    
    async def save_config_to_file(self) -> bool:
        """保存配置到文件"""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'adapters': [
                    {
                        'name': entry.name,
                        'enabled': entry.enabled,
                        'priority': entry.priority,
                        'config': entry.config
                    }
                    for entry in self.adapters.values()
                ]
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Saved {len(self.adapters)} adapter configurations to {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config to file: {e}")
            return False
    
    def add_adapter_config(self, name: str, config: DataAdapterConfig, enabled: bool = True, priority: int = 1) -> bool:
        """添加适配器配置"""
        try:
            if name in self.adapters:
                self.logger.warning(f"Adapter {name} already exists, updating configuration")
            
            self.adapters[name] = AdapterConfigEntry(
                name=name,
                enabled=enabled,
                priority=priority,
                config=config
            )
            
            self.logger.info(f"Added adapter configuration: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add adapter config {name}: {e}")
            return False
    
    def remove_adapter_config(self, name: str) -> bool:
        """移除适配器配置"""
        try:
            if name not in self.adapters:
                self.logger.warning(f"Adapter {name} not found")
                return False
            
            del self.adapters[name]
            self.logger.info(f"Removed adapter configuration: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove adapter config {name}: {e}")
            return False
    
    def get_adapter_config(self, name: str) -> Optional[AdapterConfigEntry]:
        """获取适配器配置"""
        return self.adapters.get(name)
    
    def get_enabled_adapters(self) -> List[AdapterConfigEntry]:
        """获取启用的适配器配置列表（按优先级排序）"""
        enabled_adapters = [
            entry for entry in self.adapters.values() 
            if entry.enabled
        ]
        return sorted(enabled_adapters, key=lambda x: x.priority)
    
    def get_adapters_by_type(self, source_type: DataSourceType) -> List[AdapterConfigEntry]:
        """根据数据源类型获取适配器配置"""
        return [
            entry for entry in self.adapters.values()
            if entry.enabled and entry.config.source_type == source_type
        ]
    
    def update_adapter_priority(self, name: str, priority: int) -> bool:
        """更新适配器优先级"""
        try:
            if name not in self.adapters:
                self.logger.error(f"Adapter {name} not found")
                return False
            
            self.adapters[name].priority = priority
            self.logger.info(f"Updated priority for adapter {name} to {priority}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update priority for adapter {name}: {e}")
            return False
    
    def enable_adapter(self, name: str) -> bool:
        """启用适配器"""
        try:
            if name not in self.adapters:
                self.logger.error(f"Adapter {name} not found")
                return False
            
            self.adapters[name].enabled = True
            self.logger.info(f"Enabled adapter: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable adapter {name}: {e}")
            return False
    
    def disable_adapter(self, name: str) -> bool:
        """禁用适配器"""
        try:
            if name not in self.adapters:
                self.logger.error(f"Adapter {name} not found")
                return False
            
            self.adapters[name].enabled = False
            self.logger.info(f"Disabled adapter: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable adapter {name}: {e}")
            return False
    
    def validate_all_configs(self) -> Dict[str, List[str]]:
        """验证所有配置"""
        validation_results = {}
        
        for name, entry in self.adapters.items():
            errors = []
            
            # 验证配置对象
            try:
                # 这里可以添加更多的配置验证逻辑
                if entry.config.source_type == DataSourceType.RAW_DATA:
                    if not hasattr(entry.config, 'data_directory'):
                        errors.append("RAW_DATA adapter missing data_directory")
                    elif not Path(entry.config.data_directory).exists():
                        errors.append(f"Data directory does not exist: {entry.config.data_directory}")
                
                # 验证其他配置参数
                if entry.config.update_frequency < 1:
                    errors.append("update_frequency must be >= 1")
                
                if entry.config.max_retries < 1 or entry.config.max_retries > 10:
                    errors.append("max_retries must be between 1 and 10")
                
                if entry.config.timeout < 5 or entry.config.timeout > 300:
                    errors.append("timeout must be between 5 and 300 seconds")
                
                if entry.config.quality_threshold < 0.0 or entry.config.quality_threshold > 1.0:
                    errors.append("quality_threshold must be between 0.0 and 1.0")
                
            except Exception as e:
                errors.append(f"Configuration validation error: {str(e)}")
            
            validation_results[name] = errors
        
        return validation_results
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        enabled_count = sum(1 for entry in self.adapters.values() if entry.enabled)
        disabled_count = len(self.adapters) - enabled_count
        
        source_types = {}
        for entry in self.adapters.values():
            source_type = entry.config.source_type
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        return {
            "total_adapters": len(self.adapters),
            "enabled_adapters": enabled_count,
            "disabled_adapters": disabled_count,
            "source_types": source_types,
            "config_file": self.config_file,
            "adapters": [
                {
                    "name": entry.name,
                    "enabled": entry.enabled,
                    "priority": entry.priority,
                    "source_type": entry.config.source_type,
                    "update_frequency": entry.config.update_frequency,
                    "cache_enabled": entry.config.cache_enabled
                }
                for entry in self.adapters.values()
            ]
        }
