"""
web_quote_validator 工具测试

测试 Web 行情验证器的各项功能。
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestWebQuoteValidatorUnit:
    """web_quote_validator 单元测试"""

    def test_import(self):
        """测试工具导入"""
        from openclaw_stock.tools.web_quote_validator import web_quote_validator_tool
        assert callable(web_quote_validator_tool)

    def test_format_symbol_eastmoney(self):
        """测试东方财富格式"""
        from openclaw_stock.tools.web_quote_validator import WebQuoteValidator

        validator = WebQuoteValidator(source="eastmoney")

        # 深圳股票
        assert validator._format_symbol("000001", "sz") == "0.000001"
        # 上海股票
        assert validator._format_symbol("600000", "sh") == "1.600000"
        # 港股
        assert validator._format_symbol("00700", "hk") == "116.00700"

    def test_format_symbol_tencent(self):
        """测试腾讯格式"""
        from openclaw_stock.tools.web_quote_validator import WebQuoteValidator

        validator = WebQuoteValidator(source="tencent")

        assert validator._format_symbol("000001", "sz") == "sz000001"
        assert validator._format_symbol("600000", "sh") == "sh600000"

    def test_format_symbol_sina(self):
        """测试新浪格式"""
        from openclaw_stock.tools.web_quote_validator import WebQuoteValidator

        validator = WebQuoteValidator(source="sina")

        assert validator._format_symbol("000001", "sz") == "sz000001"
        assert validator._format_symbol("600000", "sh") == "sh600000"

    def test_validate_against_reference_valid(self):
        """测试通过的价格验证"""
        from openclaw_stock.tools.web_quote_validator import WebQuoteValidator

        validator = WebQuoteValidator()

        result = validator.validate_against_reference(
            web_price=10.25,
            reference_price=10.26,
            symbol="000001",
            threshold=0.5
        )

        assert result["is_valid"] is True
        assert result["web_price"] == 10.25
        assert result["reference_price"] == 10.26
        assert abs(result["diff_pct"] - 0.0975) < 0.001
        assert "warning" not in result

    def test_validate_against_reference_invalid(self):
        """测试失败的价格验证"""
        from openclaw_stock.tools.web_quote_validator import WebQuoteValidator

        validator = WebQuoteValidator()

        result = validator.validate_against_reference(
            web_price=10.00,
            reference_price=11.00,
            symbol="000001",
            threshold=0.5
        )

        assert result["is_valid"] is False
        assert result["diff_pct"] == pytest.approx(9.0909, abs=0.001)
        assert "warning" in result
        assert "[DATA_MISMATCH_WARNING]" in result["warning"]

    def test_validate_against_reference_zero_price(self):
        """测试参考价格为0的情况"""
        from openclaw_stock.tools.web_quote_validator import WebQuoteValidator

        validator = WebQuoteValidator()

        result = validator.validate_against_reference(
            web_price=10.25,
            reference_price=0,
            symbol="000001"
        )

        assert result["is_valid"] is False
        assert result["diff_pct"] is None
        assert "[DATA_MISMATCH_WARNING]" in result["warning"]


@pytest.mark.integration
@pytest.mark.network
class TestWebQuoteValidatorIntegration:
    """web_quote_validator 集成测试（需要网络连接）"""

    @pytest.fixture(autouse=True)
    def setup_env(self, mock_env_vars):
        """设置测试环境"""
        pass

    def test_get_realtime_quote_eastmoney(self):
        """测试从东方财富获取实时行情"""
        from openclaw_stock.tools.web_quote_validator import web_quote_validator_tool

        result = web_quote_validator_tool(
            symbol="000001",
            market="sz",
            source="eastmoney"
        )

        assert result is not None
        assert result["symbol"] == "000001"
        assert result["market"] == "sz"
        assert result["source"] == "eastmoney"
        assert "name" in result
        assert "price" in result
        assert isinstance(result["price"], (int, float))
        assert result["price"] > 0

    def test_get_realtime_quote_tencent(self):
        """测试从腾讯财经获取实时行情"""
        from openclaw_stock.tools.web_quote_validator import web_quote_validator_tool

        result = web_quote_validator_tool(
            symbol="600000",
            market="sh",
            source="tencent"
        )

        assert result is not None
        assert result["symbol"] == "600000"
        assert result["market"] == "sh"
        assert result["source"] == "tencent"

    def test_get_realtime_quote_sina(self):
        """测试从新浪财经获取实时行情"""
        from openclaw_stock.tools.web_quote_validator import web_quote_validator_tool

        result = web_quote_validator_tool(
            symbol="00700",
            market="hk",
            source="sina"
        )

        assert result is not None
        assert result["symbol"] == "00700"
        assert result["market"] == "hk"
        assert result["source"] == "sina"

    def test_price_validation_with_reference(self):
        """测试带参考价格验证的完整流程"""
        from openclaw_stock.tools.web_quote_validator import web_quote_validator_tool

        # 先获取一个参考价格（模拟从 AkShare 获取）
        reference_price = 10.25

        # 获取 Web 价格并验证
        result = web_quote_validator_tool(
            symbol="000001",
            market="sz",
            source="eastmoney",
            reference_price=reference_price,
            threshold=0.5
        )

        assert result is not None
        assert "validation" in result

        validation = result["validation"]
        assert "is_valid" in validation
        assert "web_price" in validation
        assert "reference_price" in validation
        assert validation["reference_price"] == reference_price

        # 根据验证结果输出信息
        if validation["is_valid"]:
            print(f"✓ 价格验证通过，差异: {validation['diff_pct']}%")
        else:
            print(f"⚠ 价格验证警告: {validation.get('warning', '')}")


@pytest.mark.unit
class TestWebQuoteValidatorMock:
    """使用 Mock 的单元测试（无需网络）"""

    @patch('openclaw_stock.tools.web_quote_validator.WebQuoteValidator._fetch_eastmoney_realtime')
    def test_get_realtime_with_mock(self, mock_fetch):
        """使用 Mock 测试实时行情获取"""
        from openclaw_stock.tools.web_quote_validator import web_quote_validator_tool

        # 设置 Mock 返回值
        mock_fetch.return_value = {
            "source": "eastmoney",
            "symbol": "000001",
            "market": "sz",
            "name": "平安银行",
            "price": 10.25,
            "change": 0.15,
            "change_pct": 1.48,
            "volume": 152345600,
            "amount": 1562345678.90,
            "open": 10.10,
            "high": 10.30,
            "low": 10.05,
            "pre_close": 10.10,
            "timestamp": "2024-01-15T14:30:00",
        }

        result = web_quote_validator_tool(
            symbol="000001",
            market="sz",
            source="eastmoney"
        )

        assert result['name'] == '平安银行'
        assert result['price'] == 10.25
        mock_fetch.assert_called_once()


if __name__ == '__main__':
    # 直接运行测试
    pytest.main([__file__, '-v'])
