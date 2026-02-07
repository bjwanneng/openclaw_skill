#!/usr/bin/env python3
"""简洁的接口测试脚本"""
import sys
sys.path.insert(0, 'src')

def test_interface(name, test_func):
    """测试单个接口"""
    try:
        result = test_func()
        if result:
            print(f"  [OK] {name}")
            return True
        else:
            print(f"  [FAIL] {name} - 返回数据异常")
            return False
    except Exception as e:
        print(f"  [FAIL] {name} - {str(e)[:50]}")
        return False

def main():
    print("=" * 60)
    print("接口测试结果")
    print("=" * 60)

    success = []
    failed = []

    # 1. fetch_market_data
    def test1():
        from openclaw_stock.data.market_data import fetch_market_data
        df = fetch_market_data('000001', market='sz', period='daily',
                              start_date='20240101', end_date='20240131')
        return df is not None and not df.empty

    if test_interface("1. fetch_market_data", test1):
        success.append("fetch_market_data")
    else:
        failed.append("fetch_market_data")

    # 2. calculate_technical_indicators
    def test2():
        import pandas as pd
        import numpy as np
        from openclaw_stock import calculate_technical_indicators

        df = pd.DataFrame({
            'open': np.random.uniform(10, 12, 30),
            'high': np.random.uniform(11, 13, 30),
            'low': np.random.uniform(9, 11, 30),
            'close': np.random.uniform(10, 12, 30),
            'volume': np.random.randint(1000000, 5000000, 30)
        })

        result = calculate_technical_indicators(df)
        return 'ma5' in result.columns

    if test_interface("2. calculate_technical_indicators", test2):
        success.append("calculate_technical_indicators")
    else:
        failed.append("calculate_technical_indicators")

    # 3. analyze_stock
    def test3():
        from openclaw_stock import analyze_stock
        result = analyze_stock('000001', market='sz')
        return result and 'symbol' in result

    if test_interface("3. analyze_stock", test3):
        success.append("analyze_stock")
    else:
        failed.append("analyze_stock")

    # 4. calculate_support_resistance
    def test4():
        import pandas as pd
        import numpy as np
        from openclaw_stock import calculate_support_resistance

        dates = pd.date_range('2024-01-01', periods=60, freq='D')
        df = pd.DataFrame({
            'open': 10 + np.random.randn(60).cumsum() * 0.1,
            'high': 10 + np.random.randn(60).cumsum() * 0.1 + 0.5,
            'low': 10 + np.random.randn(60).cumsum() * 0.1 - 0.5,
            'close': 10 + np.random.randn(60).cumsum() * 0.1,
            'volume': np.random.randint(1000000, 5000000, 60)
        })

        result = calculate_support_resistance('000001', df, method='fibonacci')
        return 'support_levels' in result

    if test_interface("4. calculate_support_resistance", test4):
        success.append("calculate_support_resistance")
    else:
        failed.append("calculate_support_resistance")

    # 输出结果
    print()
    print("=" * 60)
    print(f"测试结果: 成功 {len(success)}/10, 失败 {len(failed)}/10")
    print("=" * 60)

    if success:
        print("成功接口:", ", ".join(success))
    if failed:
        print("失败接口:", ", ".join(failed))

    print()
    print("方案A (Pydantic v1 + 纯字典模型) 最终评估:")
    if len(success) >= 8:
        print("[OK] 方案A非常成功! 大部分接口正常工作")
    elif len(success) >= 5:
        print("[OK] 方案A部分成功, 核心功能可用")
    else:
        print("[FAIL] 方案A效果有限, 需要其他方案")

    return len(success), len(failed)

if __name__ == "__main__":
    success_count, fail_count = main()
    sys.exit(0 if fail_count == 0 else 1)
