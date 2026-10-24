-- Test trigger by inserting sample data
-- This test verifies that the calculate_indicators trigger works correctly

INSERT INTO hkex_raw_data (
    date, trading_volume, advanced_stocks, declined_stocks,
    unchanged_stocks, turnover_hkd, deals, morning_close,
    afternoon_close, change_value, change_percent
) VALUES (
    '2025-12-29', 8273, 3094, 7016, 3625, 328118569834,
    4827115, 25460.16, 25496.55, -120.87, -0.47
);

-- Wait 1 second for trigger to process
-- Then check if indicators were calculated
SELECT * FROM market_indicators WHERE date = '2025-12-29';

-- Expected: One row with calculated advance_decline_ratio, sentiment_score, etc.
-- Expected values:
-- - advance_decline_ratio ≈ 3094 / 7017 ≈ 0.44
-- - sentiment_score should be positive (based on formula)
