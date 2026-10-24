# Change: Enable VectorBT GPU Acceleration with CuPy Integration

## Why
當前的VectorBT系統僅使用CPU進行計算，雖然已經達到1,985.6策略/秒的優異性能，但通過啟用GPU加速可以進一步提升性能10-50倍，特別是在大規模參數優化（0-300完整範圍）和複雜策略計算方面。VectorBT原生支持GPU加速，只需安裝CuPy並正確配置即可發揮GPU的全部潛力。

## What Changes
- **安裝CuPy依賴** - 配置CuPy-CUDA11x支持NVIDIA GPU加速
- **GPU配置檢測** - 自動檢測GPU可用性並回退到CPU
- **VectorBT GPU集成** - 修改VectorBT引擎使用GPU數組操作
- **內存管理優化** - 實現GPU內存分配和數據傳輸優化
- **性能監控** - 添加GPU利用率監控和性能基準測試

## Impact
- **Affected specs**: gpu-acceleration, vectorbt-engine, performance-optimization
- **Affected code**:
  - `simplified_system/src/backtest/vectorbt_engine.py`
  - `simplified_system/src/backtest/enhanced_vectorbt_engine.py`
  - `simplified_system/requirements.txt`
  - GPU performance monitoring modules

## Expected Benefits
- **性能提升** - GPU加速預期提升10-50倍計算速度
- **更大規模** - 支持完整的198,900策略測試（vs 當前15,000限制）
- **成本效益** - 更短時間完成更多策略測試
- **技術先進性** - 達到頂級量化基金公司的計算能力

## Risk Mitigation
- **回退機制** - GPU不可用時自動回退到CPU模式
- **內存管理** - 防止GPU內存溢出和數據傳輸瓶頸
- **兼容性** - 保持與現有CPU代碼的完全兼容性