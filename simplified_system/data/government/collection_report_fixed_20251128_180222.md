
# 香港政府金融数据爬虫报告 - 修复版
**采集时间**: 2025-11-28 18:02:22

## 📊 采集结果汇总
- **数据源总数**: 8
- **成功采集**: 8
- **失败采集**: 0
- **成功率**: 100.0%
- **总记录数**: 8

## ✅ 成功数据源

### hkd_forward_exchange_daily
- **Data Type**: forward_exchange_rates
- **Record Count**: 1
- **API Endpoint**: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hkd-fer-daily
- **Collection Time**: 2025-11-28T18:02:07.937084

### monetary_base_daily
- **Data Type**: monetary_base
- **Record Count**: 1
- **API Endpoint**: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base
- **Collection Time**: 2025-11-28T18:02:07.936338

### market_operation_daily
- **Data Type**: market_operations
- **Record Count**: 1
- **API Endpoint**: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base
- **Collection Time**: 2025-11-28T18:02:07.945116

### efbn_yield_daily
- **Data Type**: efbn_yields, Extra Parameters: {'segment': 'IndicativePrice'}
- **Record Count**: 1
- **API Endpoint**: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/efbn-indicative-price
- **Collection Time**: 2025-11-28T18:02:07.591774

### hk_interbank_ir_daily
- **Data Type**: hibor_rates
- **Record Count**: 1
- **API Endpoint**: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily
- **Collection Time**: 2025-11-28T18:02:07.908201

### discount_window_rates_daily
- **Data Type**: discount_window_rates
- **Record Count**: 1
- **API Endpoint**: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity
- **Collection Time**: 2025-11-28T18:02:22.609458

### exchange_rates_daily
- **Data Type**: exchange_rates
- **Record Count**: 1
- **API Endpoint**: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily
- **Collection Time**: 2025-11-28T18:02:21.864008

### institutional_bond_daily
- **Data Type**: institutional_bonds, Extra Parameters: {'segment': 'Bills'}
- **Record Count**: 1
- **API Endpoint**: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/efbn-closing
- **Collection Time**: 2025-11-28T18:02:20.689620

## 📁 数据文件位置
- **完整结果**: data/government/hk_gov_financial_data_fixed_20251128_180222.json
- **分数据源文件**: data/government/[source_name]_fixed_20251128_180222.json

## 🎯 修复说明
- 修复了EFBN API，添加了 `segment=IndicativePrice` 参数
- 修复了机构债券API，添加了 `segment=Bills` 参数
- 现在可以100%成功获取所有8个数据源

## 🔄 下次建议采集时间
strftime('2025-11-29 18:02:22')
