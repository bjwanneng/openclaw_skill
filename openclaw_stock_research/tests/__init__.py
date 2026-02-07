"""
测试包初始化

测试目录结构：
- README.md: 测试说明文档
- test_ak_market_tool.py: ak_market_tool 工具测试
- test_web_quote_validator.py: web_quote_validator 工具测试
- conftest.py: pytest 共享配置和 fixture
"""

import os
import sys

# 确保测试时可以导入项目代码
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
