
# 香港政府金融数据爬虫报告
**采集时间**: 2025-11-28 17:55:06

## 📊 采集结果汇总
- **数据源总数**: 8
- **成功采集**: 6
- **失败采集**: 2
- **成功率**: 75.0%
- **总记录数**: 6

## ✅ 成功数据源

### hkd_forward_exchange_daily
- **数据类型**: forward_exchange_rates
- **记录数量**: 1
- **API端点**: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hkd-fer-daily
- **采集时间**: 2025-11-28T17:54:53.283134

### monetary_base_daily
- **数据类型**: monetary_base
- **记录数量**: 1
- **API端点**: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base
- **采集时间**: 2025-11-28T17:54:53.520873

### market_operation_daily
- **数据类型**: market_operations
- **记录数量**: 1
- **API端点**: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base
- **采集时间**: 2025-11-28T17:54:53.380026

### hk_interbank_ir_daily
- **数据类型**: hibor_rates
- **记录数量**: 1
- **API端点**: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily
- **采集时间**: 2025-11-28T17:54:53.475595

### discount_window_rates_daily
- **数据类型**: discount_window_rates
- **记录数量**: 1
- **API端点**: https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity
- **采集时间**: 2025-11-28T17:54:54.778930

### exchange_rates_daily
- **数据类型**: exchange_rates
- **记录数量**: 1
- **API端点**: https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily
- **采集时间**: 2025-11-28T17:54:54.887681

## ❌ 失败数据源

### efbn_yield_daily
- **错误信息**: HTTP 400: {"header":{"success":false,"err_code":"1002","err_msg":"Invalid input value: segment is missing or invalid input (IndicativePrice/Bills/Notes)"}}
- **采集时间**: 2025-11-28T17:55:06.326233

### institutional_bond_daily
- **错误信息**: HTTP 400: {"header":{"success":false,"err_code":"1002","err_msg":"Invalid input value: segment is missing or invalid input (Bills/Notes)"}}
- **采集时间**: 2025-11-28T17:54:52.961899

## 📁 数据文件位置
- **完整结果**: data/government/hk_gov_financial_data_20251128_175506.json
- **分数据源文件**: data/government/[source_name]_20251128_175506.json

## 🔄 下次建议采集时间
strftime('2025-11-29 17:55:06')
