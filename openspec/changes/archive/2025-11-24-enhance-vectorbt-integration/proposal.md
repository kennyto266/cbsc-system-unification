# Change: Enhance VectorBT Integration in Simplified System

## Why
完善Simplified System的VectorBT集成，提升量化交易回測性能和準確性。當前系統已經具備基礎的VectorBT功能，但通過深度集成可以發揮VectorBT的完整潛力，實現向量化計算、高性能並行處理和專業級回測分析。

## What Changes
- **增強向量化策略計算** - 替換現有手動計算為VectorBT原生向量化操作
- **優化參數優化引擎** - 利用VectorBT的內建優化功能提升大規模參數搜索效率
- **完善風險管理系統** - 集成VectorBT的專業風險指標和資金管理模型
- **增強性能分析工具** - 添加VectorBT的高級性能指標和可視化功能

## Impact
- **Affected specs**: backtest-engine, technical-indicators, parameter-optimization
- **Affected code**:
  - `simplified_system/src/backtest/vectorbt_engine.py`
  - `simplified_system/src/backtest/strategy_builder.py`
  - `simplified_system/src/indicators/core_indicators.py`
  - `simplified_system/src/backtest/enhanced_vectorbt_engine.py`

## Expected Benefits
- **性能提升** - 向量化計算預計提升3-5倍回測速度
- **功能擴展** - 支持更複雜的組合策略和風險管理
- **專業指標** - 標準化機構級回測指標和風險度量
- **可擴展性** - 為未來多資產組合優化奠定基礎