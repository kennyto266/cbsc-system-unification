"""
Test CBSC Risk Manager
CBSC風險管理測試
"""

import sys
from pathlib import Path
from datetime import date, datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_cbsc_risk_manager():
    """測試CBSC風險管理器"""
    print("=== Testing CBSC Risk Manager ===")

    try:
        from risk_management.cbsc_risk import create_cbsc_risk_manager
        from models.cbsc_models import create_sample_cbsc_contract, CBSCPortfolioPosition

        # 創建風險管理器
        risk_manager = create_cbsc_risk_manager()
        print("OK: CBSC Risk Manager created")

        # 創建測試倉位
        contract = create_sample_cbsc_contract()
        position = CBSCPortfolioPosition(
            contract=contract,
            quantity=10000,
            entry_price=2.5,
            entry_date=datetime.now(),
            current_price=2.6
        )

        # 測試收回風險
        call_risk = risk_manager.calculate_call_risk(contract, 2.6)
        print(f"OK: Call risk calculated - Distance: {call_risk['distance_to_call']:.2%}, Risk: {call_risk['risk_level']}")

        # 測試時間衰減風險
        current_date = date.today()
        time_risk = risk_manager.calculate_time_decay_risk(contract, current_date)
        print(f"OK: Time decay risk calculated - Days to maturity: {time_risk['days_to_maturity']}, Risk: {time_risk['risk_level']}")

        # 測試槓桿風險
        leverage_risk = risk_manager.calculate_leverage_risk(position)
        print(f"OK: Leverage risk calculated - Current leverage: {leverage_risk['current_leverage']:.1f}x, Risk: {leverage_risk['risk_level']}")

        # 測試綜合風險
        comprehensive_risk = risk_manager.calculate_comprehensive_risk(position, current_date)
        print(f"OK: Comprehensive risk calculated - Score: {comprehensive_risk['overall_risk_score']:.3f}, Risk: {comprehensive_risk['risk_level']}")

        # 測試倉位驗證
        validation = risk_manager.validate_position_size(contract, 50000, 1000000)
        print(f"OK: Position validation - Valid: {validation['valid']}, Ratio: {validation.get('position_ratio', 0):.2%}")

        # 測試風險報告
        risk_report = risk_manager.generate_risk_report([position], current_date)
        print(f"OK: Risk report generated - Portfolio risk: {risk_report['overall_portfolio_risk']}")

        return True

    except Exception as e:
        print(f"FAIL: CBSC Risk Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_scenarios():
    """測試風險場景"""
    print("\n=== Testing Risk Scenarios ===")

    try:
        from risk_management.cbsc_risk import create_cbsc_risk_manager
        from models.cbsc_models import CBSCContract, CBSCPortfolioPosition, CBSCType
        from datetime import date, datetime

        risk_manager = create_cbsc_risk_manager()

        # 測試接近收回價的風險場景
        near_call_contract = CBSCContract(
            ticker="99999.HK",
            underlying_ticker="0700.HK",
            cbsc_type=CBSCType.BULL,
            issuer="TEST",
            call_price=180.0,
            strike_price=200.0,
            entitlement_ratio=0.1,
            leverage_ratio=8.0,
            issue_date=date(2024, 1, 1),
            maturity_date=date(2025, 12, 31),
            listing_date=date(2024, 1, 2)
        )

        near_call_position = CBSCPortfolioPosition(
            contract=near_call_contract,
            quantity=10000,
            entry_price=2.0,
            entry_date=datetime.now(),
            current_price=185.0  # 非常接近收回價
        )

        # 計算風險
        risk_analysis = risk_manager.calculate_comprehensive_risk(near_call_position, date.today())
        print(f"OK: Near-call risk scenario - Risk Level: {risk_analysis['risk_level']}")
        print(f"  Call distance: {risk_analysis['risk_components']['call_risk']['distance_to_call']:.2%}")
        print(f"  Recommendation: {risk_analysis['recommendation']}")

        # 測試高槓桿風險場景
        high_leverage_contract = CBSCContract(
            ticker="88888.HK",
            underlying_ticker="0700.HK",
            cbsc_type=CBSCType.BEAR,
            issuer="TEST",
            call_price=150.0,
            strike_price=120.0,
            entitlement_ratio=0.05,
            leverage_ratio=15.0,  # 非常高的槓桿
            issue_date=date(2024, 1, 1),
            maturity_date=date(2025, 12, 31),
            listing_date=date(2024, 1, 2)
        )

        high_leverage_position = CBSCPortfolioPosition(
            contract=high_leverage_contract,
            quantity=20000,
            entry_price=1.5,
            entry_date=datetime.now(),
            current_price=1.3  # 虧損狀態
        )

        leverage_risk = risk_manager.calculate_leverage_risk(high_leverage_position)
        print(f"OK: High leverage scenario - Leverage: {leverage_risk['current_leverage']:.1f}x")
        print(f"  Utilization: {leverage_risk['leverage_utilization']:.2%}")
        print(f"  Risk Level: {leverage_risk['risk_level']}")

        return True

    except Exception as e:
        print(f"FAIL: Risk scenarios test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("CBSC Risk Manager Test Starting...\n")

    # 運行測試
    test_results = []

    result1 = test_cbsc_risk_manager()
    test_results.append(("CBSC Risk Manager", result1))

    result2 = test_risk_scenarios()
    test_results.append(("Risk Scenarios", result2))

    # 總結
    print("\n=== Test Results ===")
    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All CBSC risk management tests passed!")
        return True
    else:
        print("WARNING: Some CBSC risk tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)