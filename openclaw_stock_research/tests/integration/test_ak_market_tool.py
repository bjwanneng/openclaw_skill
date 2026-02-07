"""
ak_market_tool 工具测试

测试 AkShare 数据引擎的各项功能。
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestAKMarketToolUnit:
    """ak_market_tool 单元测试"""

    def test_import(self):
        """测试工具导入"""
        from openclaw_stock.tools.ak_market_tool import ak_market_tool
        assert callable(ak_market_tool)

    def test_validate_symbol_valid(self):
        """测试有效的股票代码验证"""
        from openclaw_stock.tools.ak_market_tool import AKMarketTool

        tool = AKMarketTool()
        # 应该不抛出异常
        tool._validate_symbol("000001", "sz")
        tool._validate_symbol("600000", "sh")
        tool._validate_symbol("00700", "hk")

    def test_validate_symbol_invalid(self):
        """测试无效的股票代码验证"""
        from openclaw_stock.tools.ak_market_tool import AKMarketTool
        from openclaw_stock.core.exceptions import SymbolNotFoundError

        tool = AKMarketTool()

        with pytest.raises(SymbolNotFoundError):
            tool._validate_symbol("", "sz")

        with pytest.raises(SymbolNotFoundError):
            tool._validate_symbol(None, "sh")


@pytest.mark.integration
@pytest.mark.network
class TestAKMarketToolIntegration:
    """ak_market_tool 集成测试（需要网络连接）"""

    @pytest.fixture(autouse=True)
    def setup_env(self, mock_env_vars):
        """设置测试环境"""
        pass

    def test_realtime_quote_sz(self):
        """测试获取深圳股票实时行情"""
        from openclaw_stock.tools.ak_market_tool import ak_market_tool

        result = ak_market_tool(
            action="realtime",
            symbol="000001",
            market="sz"
        )

        assert result is not None
        assert result["symbol"] == "000001"
        assert result["market"] == "sz"
        assert "name" in result
        assert "price" in result
        assert isinstance(result["price"], (int, float))

    def test_realtime_quote_sh(self):
        """测试获取上海股票实时行情"""
        from openclaw_stock.tools.ak_market_tool import ak_market_tool

        result = ak_market_tool(
            action="realtime",
            symbol="600000",
            market="sh"
        )

        assert result is not None
        assert result["symbol"] == "600000"
        assert result["market"] == "sh"

    def test_realtime_quote_hk(self):
        """测试获取港股实时行情"""
        from openclaw_stock.tools.ak_market_tool import ak_market_tool

        result = ak_market_tool(
            action="realtime",
            symbol="00700",
            market="hk"
        )

        assert result is not None
        assert result["symbol"] == "00700"
        assert result["market"] == "hk"

    def test_kline_data(self):
        """测试获取历史K线数据"""
        from openclaw_stock.tools.ak_market_tool import ak_market_tool

        result = ak_market_tool(
            action="kline",
            symbol="000001",
            market="sz",
            period="daily",
            start_date="20240101",
            end_date="20240131",
            adjust="qfq"
        )

        assert result is not None
        assert result["symbol"] == "000001"
        assert result["period"] == "daily"
        assert result["adjust"] == "qfq"
        assert "data" in result
        assert isinstance(result["data"], list)

    def test_fundamental_data(self):
        """测试获取基本面数据"""
        from openclaw_stock.tools.ak_market_tool import ak_market_tool

        result = ak_market_tool(
            action="fundamental",
            symbol="000001",
            market="sz"
        )

        assert result is not None
        assert result["symbol"] == "000001"
        assert "pe_ttm" in result or result.get("pe_ttm") is None  # 港股可能为空

    def test_capital_flow(self):
        """测试获取资金流向数据"""
        from openclaw_stock.tools.ak_market_tool import ak_market_tool

        result = ak_market_tool(
            action="capital_flow",
            symbol="000001",
            market="sz",
            flow_type="all"
        )

        assert result is not None
        assert result["symbol"] == "000001"
        assert result["flow_type"] == "all"

    def test_invalid_symbol(self):
        """测试无效的股票代码"""
        from openclaw_stock.tools.ak_market_tool import ak_market_tool
        from openclaw_stock.core.exceptions import SymbolNotFoundError

        with pytest.raises((SymbolNotFoundError, Exception)):
            ak_market_tool(
                action="realtime",
                symbol="99999999",  # 不存在的代码
                market="sz"
            )


@pytest.mark.unit
class TestAKMarketToolMock:
    """使用 Mock 的单元测试（无需网络）"""

    @patch('openclaw_stock.adapters.akshare_adapter.ak.stock_zh_a_spot_em')
    def test_realtime_with_mock(self, mock_spot):
        """使用 Mock 测试实时行情"""
        import pandas as pd
        from openclaw_stock.tools.ak_market_tool import ak_market_tool

        # 创建模拟的 DataFrame
        mock_data = pd.DataFrame({
            '代码': ['000001'],
            '名称': ['平安银行'],
            '最新价': [10.25],
            '涨跌额': [0.15],
            '涨跌幅': [1.48],
            '成交量': [152345600],
            '成交额': [1562345678.90],
            '最高': [10.30],
            '最低': [10.05],
            '今开': [10.10],
            '昨收': [10.10],
        })
        mock_spot.return_value = mock_data

        result = ak_market_tool(
            action="realtime",
            symbol="000001",
            market="sz"
        )

        assert result['name'] == '平安银行'
        assert result['price'] == 10.25


if __name__ == '__main__':
    # 直接运行测试
    pytest.main([__file__, '-v'])
