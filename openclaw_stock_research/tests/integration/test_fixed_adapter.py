#!/usr/bin/env python3
"""
测试修复后的 AkShare 适配器
"""

import sys
import os

# 添加项目源码到路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 设置环境变量
os.environ.setdefault('AKSHARE_DATA_PATH', os.path.join(project_root, 'data', 'akshare_cache'))
os.environ.setdefault('LOG_LEVEL', 'INFO')

print("=" * 70)
print("测试修复后的 AkShare 适配器")
print("=" * 70)
print()

# 测试1: 导入修复后的适配器
print("[测试1] 导入修复后的适配器...")
try:
    from openclaw_stock.adapters.akshare_adapter_fixed import AKShareAdapterFixed, get_adapter_fixed
    print("  [OK] 修复后的适配器导入成功")
except Exception as e:
    print(f"  [FAIL] 导入失败: {e}")
    sys.exit(1)

# 测试2: 创建适配器实例
print("\n[测试2] 创建适配器实例...")
try:
    adapter = get_adapter_fixed()
    print("  [OK] 适配器实例创建成功")
except Exception as e:
    print(f"  [FAIL] 创建失败: {e}")
    sys.exit(1)

# 测试3: 获取A股实时行情
print("\n[测试3] 获取A股实时行情 (使用 stock_zh_a_spot)...")
try:
    df = adapter.get_stock_zh_a_spot()
    print(f"  [OK] 成功获取 {len(df)} 条A股实时行情")
    if len(df) > 0:
        print(f"  示例数据:")
        print(f"    - 股票代码: {df.iloc[0].get('代码', 'N/A')}")
        print(f"    - 股票名称: {df.iloc[0].get('名称', 'N/A')}")
        print(f"    - 最新价格: {df.iloc[0].get('最新价', 'N/A')}")
except Exception as e:
    print(f"  [FAIL] 获取失败: {e}")
    print("  注意: 这可能是网络问题或AkShare数据源暂时不可用")

# 测试4: 获取个股历史数据
print("\n[测试4] 获取个股历史数据 (使用 stock_zh_a_daily)...")
try:
    df = adapter.get_stock_zh_a_hist(
        symbol="000001",
        period="daily",
        start_date="20240101",
        end_date="20240131",
        adjust="qfq"
    )
    print(f"  [OK] 成功获取 {len(df)} 条历史K线数据")
    if len(df) > 0:
        print(f"  示例数据:")
        print(f"    - 日期: {df.iloc[0].get('date', df.index[0])}")
        print(f"    - 开盘价: {df.iloc[0].get('open', 'N/A')}")
        print(f"    - 收盘价: {df.iloc[0].get('close', 'N/A')}")
except Exception as e:
    print(f"  [FAIL] 获取失败: {e}")
    print("  注意: 这可能是网络问题或AkShare数据源暂时不可用")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
