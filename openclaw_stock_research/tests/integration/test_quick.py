#!/usr/bin/env python3
"""
Quick test script - Verify tools can be imported
"""

import sys
from pathlib import Path

# Add project source to path
project_root = Path(__file__).parent.resolve()
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print("=" * 60)
print("OpenClaw Stock Research - Quick Test")
print("=" * 60)
print()

# Test imports
print("Testing module imports...")
try:
    from openclaw_stock.tools.ak_market_tool import ak_market_tool
    print("[OK] ak_market_tool imported successfully")
except Exception as e:
    print(f"[FAIL] ak_market_tool import failed: {e}")

try:
    from openclaw_stock.tools.web_quote_validator import web_quote_validator_tool
    print("[OK] web_quote_validator_tool imported successfully")
except Exception as e:
    print(f"[FAIL] web_quote_validator_tool import failed: {e}")

print()
print("=" * 60)
print("Test completed")
print("=" * 60)
