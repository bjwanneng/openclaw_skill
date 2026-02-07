"""
pytest 共享配置和 fixture

此文件定义了所有测试共用的 fixture 和配置。
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 确保可以导入项目代码
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope='session')
def project_root_path():
    """返回项目根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture(scope='session')
def test_data_path(project_root_path):
    """返回测试数据目录路径"""
    path = project_root_path / 'tests' / 'data'
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope='function')
def mock_env_vars(monkeypatch):
    """设置测试用的环境变量"""
    env_vars = {
        'AKSHARE_DATA_PATH': './test_data/akshare',
        'LOG_LEVEL': 'DEBUG',
        'DEFAULT_TIMEOUT': '30',
        'PRICE_DIFF_THRESHOLD': '0.5',
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture(scope='function')
def mock_akshare_data():
    """模拟 AkShare 返回的数据"""
    return {
        'realtime': {
            'symbol': '000001',
            'name': '平安银行',
            'price': 10.25,
            'change': 0.15,
            'change_pct': 1.48,
            'volume': 152345600,
            'amount': 1562345678.90,
            'high': 10.30,
            'low': 10.05,
            'open': 10.10,
            'pre_close': 10.10,
        }
    }


@pytest.fixture(scope='function')
def mock_web_data():
    """模拟 Web 抓取返回的数据"""
    return {
        'source': 'eastmoney',
        'symbol': '000001',
        'market': 'sz',
        'name': '平安银行',
        'price': 10.26,
        'change': 0.16,
        'change_pct': 1.58,
        'volume': 152345600,
        'amount': 1562345678.90,
        'open': 10.10,
        'high': 10.30,
        'low': 10.05,
        'pre_close': 10.10,
        'timestamp': '2024-01-15T14:30:00',
    }


@pytest.fixture(scope='function')
def mock_requests_get():
    """模拟 requests.get 方法"""
    with patch('requests.Session.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rc': 0,
            'data': {
                'f43': 1025,  # 价格 * 100
                'f44': 1030,  # 最高价 * 100
                'f45': 1005,  # 最低价 * 100
                'f46': 1010,  # 开盘价 * 100
                'f47': 152345600,  # 成交量
                'f48': 1562345678,  # 成交额
                'f57': '000001',  # 代码
                'f58': '平安银行',  # 名称
                'f60': 1010,  # 昨收 * 100
                'f170': 148,  # 涨跌幅 * 100
            }
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture(scope='function')
def cleanup_test_data(test_data_path):
    """测试结束后清理测试数据"""
    yield
    # 测试后的清理工作
    import shutil
    if test_data_path.exists():
        for item in test_data_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


# 标记配置
def pytest_configure(config):
    """配置 pytest 标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "network: 需要网络连接")
    config.addinivalue_line("markers", "slow: 执行较慢的测试")


# 命令行选项
def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help="运行需要网络连接的测试"
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="运行执行较慢的测试"
    )


def pytest_collection_modifyitems(config, items):
    """根据命令行选项跳过测试"""
    run_network = config.getoption("--run-network")
    run_slow = config.getoption("--run-slow")

    skip_network = pytest.mark.skip(reason="需要 --run-network 选项")
    skip_slow = pytest.mark.skip(reason="需要 --run-slow 选项")

    for item in items:
        if "network" in item.keywords and not run_network:
            item.add_marker(skip_network)
        if "slow" in item.keywords and not run_slow:
            item.add_marker(skip_slow)
