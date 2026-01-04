// InfluxDB Retention Policies and Downsampling Tasks
// InfluxDB 數據保留策略和降採樣任務
// Phase 1.2 - 時序數據庫配置

import "influxdata/influxdb/v1"
import "experimental"
import "array"

// ===== 創建桶 (Buckets) =====

// 創建不同保留期的桶
option task = {
    name: "setup_buckets",
    every: 1h,
    offset: 5m,
}

// 創建原始市場數據桶（90天保留期）
buckets = [
    {
        name: "market_data_raw",
        description: "Raw market data with minute-level granularity",
        retentionRules: [{type: "expire", everySeconds: 7776000}], // 90 days
    },
    {
        name: "market_data_hourly",
        description: "Hourly aggregated market data",
        retentionRules: [{type: "expire", everySeconds: 63072000}], // 2 years
    },
    {
        name: "market_data_daily",
        description: "Daily aggregated market data",
        retentionRules: [{type: "expire", everySeconds: 315360000}], // 10 years
    },
    {
        name: "strategy_performance",
        description: "Strategy performance metrics and analytics",
        retentionRules: [{type: "expire", everySeconds: 15768000}], // 5 years
    },
    {
        name: "risk_metrics",
        description: "Risk calculation results and VaR/ES metrics",
        retentionRules: [{type: "expire", everySeconds: 15768000}], // 5 years
    },
    {
        name: "trading_signals",
        description: "Trading signals, orders, and execution data",
        retentionRules: [{type: "expire", everySeconds: 63072000}], // 2 years
    },
    {
        name: "system_metrics",
        description: "System performance and monitoring metrics",
        retentionRules: [{type: "expire", everySeconds: 2592000}], // 30 days
    },
]

// 批量創建桶
for bucket in buckets {
    // 檢查桶是否已存在
    existing = buckets()
        |> filter(fn: (r) => r.name == bucket.name)

    // 如果桶不存在則創建
    if length(existing) == 0 {
        bucket()
            |> set(
                orgID: "cbsc",
                name: bucket.name,
                description: bucket.description,
                retentionRules: bucket.retentionRules
            )
    }
}

// ===== 降採樣任務 (Downsampling Tasks) =====

// 任務1: 將分鐘級數據聚合為小時級數據
downsample_to_hourly = task.new(
    name: "downsample_market_data_hourly",
    every: 1h,
    offset: 5m,
    fn: (tables) => tables
        |> range(start: -2h)
        |> filter(fn: (r) => r._measurement == "stock_price")
        |> filter(fn: (r) => r._field != "quality")
        |> aggregateWindow(
            every: 1h,
            fn: (tables) => tables |> reduce(
                identity: {_value: 0.0, _time: 0, count: 0},
                fn: (r, accumulator) => ({
                    _value: if r._field == "open" then r._value
                            else if r._field == "high" and r._value > accumulator._value then r._value
                            else if r._field == "low" and (accumulator._value == 0.0 or r._value < accumulator._value) then r._value
                            else if r._field == "close" then r._value
                            else if r._field == "volume" then accumulator._value + r._value
                            else accumulator._value,
                    _time: r._time,
                    count: accumulator.count + 1
                })
            ),
            createEmpty: false,
        )
        |> drop(columns: ["count"])
        |> set(
            bucket: "market_data_hourly",
            org: "cbsc",
        )
        |> to(bucket: "market_data_hourly", org: "cbsc"),
)

// 啟動小時級降採樣任務
downsample_to_hourly
    |> tasks.trigger()

// 任務2: 將小時級數據聚合為日級數據
downsample_to_daily = task.new(
    name: "downsample_market_data_daily",
    every: 24h,
    offset: 1h,
    fn: (tables) => tables
        |> range(start: -2d)
        |> filter(fn: (r) => r._measurement == "stock_price")
        |> filter(fn: (r) => r._field != "quality")
        |> aggregateWindow(
            every: 1d,
            fn: (tables) => tables |> reduce(
                identity: {_value: 0.0, _time: 0, count: 0, _first: 0.0, _last: 0.0, _max: 0.0, _min: 999999999.0, _sum: 0.0},
                fn: (r, accumulator) => ({
                    _value: r._value,
                    _time: r._time,
                    count: accumulator.count + 1,
                    _first: if accumulator.count == 0 then r._value else accumulator._first,
                    _last: r._value,
                    _max: if r._value > accumulator._max then r._value else accumulator._max,
                    _min: if r._value < accumulator._min then r._value else accumulator._min,
                    _sum: accumulator._sum + r._value
                })
            ),
            createEmpty: false,
        )
        |> map(fn: (r) => ({
            _time: r._time,
            _measurement: r._measurement,
            _field: r._field,
            _value: if r._field == "open" then r._first
                    else if r._field == "high" then r._max
                    else if r._field == "low" then r._min
                    else if r._field == "close" then r._last
                    else if r._field == "volume" then r._sum
                    else r._value,
            symbol: r.symbol,
            exchange: r.exchange,
            currency: r.currency,
        }))
        |> set(
            bucket: "market_data_daily",
            org: "cbsc",
        )
        |> to(bucket: "market_data_daily", org: "cbsc"),
)

// 啟動日級降採樣任務
downsample_to_daily
    |> tasks.trigger()

// 任務3: 策略性能數據日級聚合
aggregate_strategy_performance = task.new(
    name: "aggregate_strategy_performance_daily",
    every: 1d,
    offset: 5m,
    fn: (tables) => tables
        |> range(start: -2d)
        |> filter(fn: (r) =>
            r._measurement == "strategy_returns" or
            r._measurement == "strategy_risk" or
            r._measurement == "strategy_ratios"
        )
        |> aggregateWindow(
            every: 1d,
            fn: mean,
            createEmpty: false,
        )
        |> set(
            bucket: "strategy_performance",
            org: "cbsc",
        )
        |> to(bucket: "strategy_performance", org: "cbsc"),
)

// 啟動策略性能聚合任務
aggregate_strategy_performance
    |> tasks.trigger()

// 任務4: 技術指標數據清理（保留最新值）
cleanup_technical_indicators = task.new(
    name: "cleanup_technical_indicators",
    every: 1d,
    offset: 2h,
    fn: (tables) => tables
        |> range(start: -30d)
        |> filter(fn: (r) => r._measurement == "technical_indicators")
        |> group(columns: ["symbol", "indicator_type", "indicator_name", "timeframe"])
        |> last(column: "_time")
        |> keep(columns: ["_measurement", "symbol", "indicator_type", "indicator_name", "timeframe", "_field", "_value", "_time"])
        |> set(
            bucket: "market_data_raw",
            org: "cbsc",
        )
        |> to(bucket: "market_data_raw", org: "cbsc"),
)

// 啟動技術指標清理任務
cleanup_technical_indicators
    |> tasks.trigger()

// 任務5: 系統指標聚合
aggregate_system_metrics = task.new(
    name: "aggregate_system_metrics",
    every: 5m,
    offset: 30s,
    fn: (tables) => tables
        |> range(start: -10m)
        |> filter(fn: (r) =>
            r._measurement == "api_performance" or
            r._measurement == "database_performance"
        )
        |> group(columns: ["_measurement", "endpoint", "method", "service", "database_type", "operation_type"])
        |> aggregateWindow(
            every: 5m,
            fn: mean,
            createEmpty: false,
        )
        |> set(
            bucket: "system_metrics",
            org: "cbsc",
        )
        |> to(bucket: "system_metrics", org: "cbsc"),
)

// 啟動系統指標聚合任務
aggregate_system_metrics
    |> tasks.trigger()

// ===== 數據清理任務 (Data Cleanup Tasks) =====

// 清理任務1: 刪除過期的市場數據
cleanup_expired_market_data = task.new(
    name: "cleanup_expired_market_data",
    every: 1d,
    offset: 3h,
    fn: (tables) => {
        // 刪除超過90天的原始市場數據
        expired_raw = from(bucket: "market_data_raw")
            |> range(start: -120d)  // 範圍擴大以確保捕獲所有過期數據
            |> filter(fn: (r) => r._measurement == "stock_price")
            |> filter(fn: (r) => r._time < experimental.subDuration(d: 90d, from: now()))

        // 執行刪除操作
        from(bucket: "market_data_raw")
            |> range(start: -120d)
            |> filter(fn: (r) => r._measurement == "stock_price")
            |> filter(fn: (r) => r._time < experimental.subDuration(d: 90d, from: now()))
            |> drop()
    },
)

// 啟動市場數據清理任務
cleanup_expired_market_data
    |> tasks.trigger()

// 清理任務2: 刪除過期的系統指標
cleanup_expired_system_metrics = task.new(
    name: "cleanup_expired_system_metrics",
    every: 1h,
    offset: 15m,
    fn: (tables) => {
        // 刪除超過30天的系統指標
        from(bucket: "system_metrics")
            |> range(start: -35d)
            |> filter(fn: (r) => r._time < experimental.subDuration(d: 30d, from: now()))
            |> drop()
    },
)

// 啟動系統指標清理任務
cleanup_expired_system_metrics
    |> tasks.trigger()

// ===== 數據質量檢查任務 (Data Quality Checks) =====

// 質量檢查1: 價格數據異常檢測
price_anomaly_detection = task.new(
    name: "price_anomaly_detection",
    every: 5m,
    offset: 1m,
    fn: (tables) => tables
        |> range(start: -10m)
        |> filter(fn: (r) => r._measurement == "stock_price")
        |> filter(fn: (r) => r._field == "close")
        |> group(columns: ["symbol", "exchange"])
        |> aggregateWindow(
            every: 5m,
            fn: (tables) => tables |> findRecord(
                fn: (key) => true,
                idx: 0
            ),
            createEmpty: false,
        )
        |> map(fn: (r) => ({
            r with
            // 計算與前一個值的百分比變化
            price_change: if exists(r._previous_value)
                then (r._value - r._previous_value) / r._previous_value * 100.0
                else 0.0,
            // 標記異常價格變化（超過20%）
            is_anomaly: if exists(r._previous_value)
                then abs((r._value - r._previous_value) / r._previous_value * 100.0) > 20.0
                else false,
        }))
        |> filter(fn: (r) => r.is_anomaly == true)
        |> set(
            _measurement: "price_anomalies",
            bucket: "system_metrics",
            org: "cbsc",
        )
        |> to(bucket: "system_metrics", org: "cbsc"),
)

// 啟動價格異常檢測任務
price_anomaly_detection
    |> tasks.trigger()

// 質量檢查2: 數據缺失檢測
data_gap_detection = task.new(
    name: "data_gap_detection",
    every: 15m,
    offset: 5m,
    fn: (tables) => tables
        |> range(start: -1h)
        |> filter(fn: (r) => r._measurement == "stock_price")
        |> filter(fn: (r) => r._field == "close")
        |> group(columns: ["symbol", "exchange"])
        |> aggregateWindow(
            every: 1m,
            fn: count,
            createEmpty: false,
        )
        |> filter(fn: (r) => r._value == 0)  // 找到缺失的數據點
        |> set(
            _measurement: "data_gaps",
            bucket: "system_metrics",
            org: "cbsc",
        )
        |> to(bucket: "system_metrics", org: "cbsc"),
)

// 啟動數據缺失檢測任務
data_gap_detection
    |> tasks.trigger()

// ===== 報告任務 (Reporting Tasks) =====

// 報告任務1: 每日數據統計
daily_data_statistics = task.new(
    name: "daily_data_statistics",
    every: 24h,
    offset: 1h,
    fn: (tables) => {
        // 市場數據統計
        market_stats = from(bucket: "market_data_raw")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "stock_price")
            |> group(columns: ["_measurement"])
            |> count()

        // 策略數據統計
        strategy_stats = from(bucket: "strategy_performance")
            |> range(start: -24h)
            |> group(columns: ["_measurement"])
            |> count()

        // 系統指標統計
        system_stats = from(bucket: "system_metrics")
            |> range(start: -24h)
            |> group(columns: ["_measurement"])
            |> count()

        // 合併統計數據
        union(tables: [market_stats, strategy_stats, system_stats])
            |> set(
                _measurement: "daily_statistics",
                bucket: "system_metrics",
                org: "cbsc",
            )
            |> to(bucket: "system_metrics", org: "cbsc")
    },
)

// 啟動每日統計任務
daily_data_statistics
    |> tasks.trigger()

// ===== 任務監控 (Task Monitoring) =====

// 監控所有任務的運行狀態
monitor_tasks = task.new(
    name: "monitor_tasks",
    every: 1h,
    offset: 30m,
    fn: (tables) => {
        taskList = tasks.list()
            |> set(
                _measurement: "task_status",
                bucket: "system_metrics",
                org: "cbsc",
            )
            |> to(bucket: "system_metrics", org: "cbsc")
    },
)

// 啟動任務監控
monitor_tasks
    |> tasks.trigger()

// 輸出設置完成信息
"✅ InfluxDB retention policies and downsampling tasks configured successfully"
    |> yield(name: "setup_complete")