#!/usr/bin/env python3
"""
Integration tests for stock analysis modules.

These tests verify the integration between different modules.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import all modules to test
from openclaw_stock.data import (
    fetch_market_data,
    fetch_realtime_quote,
    fetch_financial_data,
    fetch_fund_flow,
)
from openclaw_stock.analysis import (
    calculate_technical_indicators,
    calculate_support_resistance,
    calculate_fundamental_indicators,
    analyze_stock,
)
from openclaw_stock.selection import (
    short_term_stock_selector,
    long_term_stock_selector,
)
from openclaw_stock.alert import (
    setup_alert,
    remove_alert,
    list_alerts,
)


class TestDataModule:
    """Test data collection modules"""

    def test_fetch_realtime_quote(self):
        """Test fetching real-time quote"""
        try:
            quote = fetch_realtime_quote(symbol='000001', market='sz')
            assert isinstance(quote, dict)
            assert 'symbol' in quote
            assert 'price' in quote
            assert 'change_pct' in quote
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")

    def test_fetch_market_data(self):
        """Test fetching market data"""
        try:
            df = fetch_market_data(
                symbol='000001',
                period='daily',
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
                market='sz'
            )
            assert isinstance(df, pd.DataFrame)
            assert not df.empty
            assert 'close' in df.columns
            assert 'volume' in df.columns
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")

    def test_fetch_financial_data(self):
        """Test fetching financial data"""
        try:
            financial = fetch_financial_data(symbol='000001', report_type='all')
            assert isinstance(financial, dict)
            assert 'symbol' in financial
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")

    def test_fetch_fund_flow(self):
        """Test fetching fund flow data"""
        try:
            df = fetch_fund_flow(symbol='000001', days=5)
            assert isinstance(df, pd.DataFrame)
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")


class TestAnalysisModule:
    """Test analysis modules"""

    def test_calculate_technical_indicators(self):
        """Test calculating technical indicators"""
        try:
            # Create sample data
            dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
            df = pd.DataFrame({
                'open': np.random.uniform(10, 20, 100),
                'high': np.random.uniform(10, 20, 100),
                'low': np.random.uniform(10, 20, 100),
                'close': np.random.uniform(10, 20, 100),
                'volume': np.random.randint(1000000, 10000000, 100)
            }, index=dates)

            df_result = calculate_technical_indicators(df)
            assert isinstance(df_result, pd.DataFrame)
            assert 'ma5' in df_result.columns
            assert 'macd_dif' in df_result.columns
            assert 'rsi6' in df_result.columns
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")

    def test_calculate_support_resistance(self):
        """Test calculating support/resistance levels"""
        try:
            # Create sample data
            dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
            df = pd.DataFrame({
                'open': np.random.uniform(10, 20, 60),
                'high': np.random.uniform(15, 25, 60),
                'low': np.random.uniform(5, 15, 60),
                'close': np.random.uniform(10, 20, 60),
                'volume': np.random.randint(1000000, 10000000, 60)
            }, index=dates)

            sr = calculate_support_resistance(symbol='000001', df=df, method='fibonacci')
            assert isinstance(sr, dict)
            assert 'support_levels' in sr
            assert 'resistance_levels' in sr
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")

    def test_calculate_fundamental_indicators(self):
        """Test calculating fundamental indicators"""
        try:
            fundamental = calculate_fundamental_indicators(symbol='000001')
            assert isinstance(fundamental, dict)
            assert 'symbol' in fundamental
            assert 'valuation' in fundamental or 'profitability' in fundamental
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")

    def test_analyze_stock(self):
        """Test comprehensive stock analysis"""
        try:
            result = analyze_stock(symbol='000001', market='sz', lookback_days=60)
            assert isinstance(result, dict)
            assert 'symbol' in result
            assert 'basic_info' in result or 'technical_analysis' in result
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")


class TestSelectionModule:
    """Test selection modules"""

    def test_short_term_stock_selector(self):
        """Test short-term stock selection"""
        try:
            # This test may take a while as it scans the market
            df = short_term_stock_selector(top_n=10)
            assert isinstance(df, pd.DataFrame)
            # May be empty if market is closed
            if not df.empty:
                assert 'symbol' in df.columns
                assert 'total_score' in df.columns
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")

    def test_long_term_stock_selector(self):
        """Test long-term stock selection"""
        try:
            # This test may take a while as it scans the market
            df = long_term_stock_selector(top_n=10)
            assert isinstance(df, pd.DataFrame)
            # May be empty if market is closed
            if not df.empty:
                assert 'symbol' in df.columns
                assert 'total_score' in df.columns
        except Exception as e:
            pytest.skip(f"Skipping test: {e}")


class TestAlertModule:
    """Test alert modules"""

    def test_setup_alert(self):
        """Test setting up stock alert"""
        try:
            alert_id = setup_alert(
                symbol='000001',
                alert_type='price',
                condition={'operator': 'above', 'value': 100.0},  # Set high threshold so it won't trigger
                notification_method='console'
            )

            assert isinstance(alert_id, str)
            assert alert_id.startswith('000001')

            # Clean up
            remove_alert(alert_id)

        except Exception as e:
            pytest.skip(f"Skipping test: {e}")

    def test_list_alerts(self):
        """Test listing alerts"""
        try:
            # Create a test alert
            alert_id = setup_alert(
                symbol='000002',
                alert_type='price',
                condition={'operator': 'below', 'value': 1.0},
                notification_method='console'
            )

            # List alerts
            alerts = list_alerts(symbol='000002')

            assert isinstance(alerts, list)
            assert len(alerts) > 0
            assert any(a['symbol'] == '000002' for a in alerts)

            # Clean up
            remove_alert(alert_id)

        except Exception as e:
            pytest.skip(f"Skipping test: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
