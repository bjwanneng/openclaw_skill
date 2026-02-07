#!/usr/bin/env python3
"""
测试东方财富版本适配器
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
print("测试东方财富版本适配器")
print("=" * 70)
print()

# 导入适配器
try:
    from openclaw_stock.adapters.akshare_adapter_em import AKShareAdapterEM, get_adapter_em
    print("[OK] 适配器导入成功")
except Exception as e:
    print(f"[FAIL] 适配器导入失败: {e}")
    sys.exit(1)

# 创建适配器实例
try:
    adapter = get_adapter_em()
    print("[OK] 适配器实例创建成功")
except Exception as e:
    print(f"[FAIL] 适配器实例创建失败: {e}")
    sys.exit(1)

# 测试1: 获取A股实时行情
print("\n[测试1] 获取A股实时行情...")
try:
    df = adapter.get_stock_zh_a_spot_em()
    print(f"[OK] 成功获取 {len(df)} 条A股实时行情")
    if len(df) > 0:
        print(f"  示例: {df.iloc[0]['代码']} - {df.iloc[0]['名称']} - 价格:{df.iloc[0]['最新价']}")
except Exception as e:
    print(f"[FAIL] 获取失败: {e}")

# 测试2: 获取A股历史数据
print("\n[测试2] 获取A股历史数据...")
try:
    df = adapter.get_stock_zh_a_hist_em(
        symbol="000001",
        period="daily",
        start_date="20240101",
        end_date="20240110",
        adjust="qfq"
    )
    print(f"[OK] 成功获取 {len(df)} 条历史K线数据")
    if len(df) > 0:
        print(f"  示例日期: {df.iloc[0]['日期']}, 收盘价: {df.iloc[0]['收盘']}")
except Exception as e:
    print(f"[FAIL] 获取失败: {e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
