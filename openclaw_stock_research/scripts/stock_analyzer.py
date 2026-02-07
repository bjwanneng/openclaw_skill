#!/usr/bin/env python3
"""
Stock Analyzer Script

Command-line interface for stock analysis and selection.

Usage:
    python stock_analyzer.py analyze <symbol> [--market <market>]
    python stock_analyzer.py select-short [--top-n <n>]
    python stock_analyzer.py select-long [--top-n <n>]
    python stock_analyzer.py alert-setup <symbol> <type> <condition>

Examples:
    python stock_analyzer.py analyze 000001 --market sz
    python stock_analyzer.py select-short --top-n 50
    python stock_analyzer.py alert-setup 000001 price "above:15.0"
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.openclaw_stock import (
    analyze_stock,
    short_term_stock_selector,
    long_term_stock_selector,
    setup_alert,
    fetch_realtime_quote,
)


def cmd_analyze(args):
    """Analyze a single stock"""
    print(f"Analyzing {args.market}:{args.symbol}...")

    try:
        result = analyze_stock(
            symbol=args.symbol,
            market=args.market,
            lookback_days=args.lookback
        )

        # Print summary
        basic = result.get('basic_info', {})
        prediction = result.get('prediction', {})

        print("\n" + "="*60)
        print(f"股票: {basic.get('name', 'N/A')} ({args.symbol})")
        print(f"当前价格: {basic.get('current_price', 'N/A')}")
        print(f"涨跌幅: {basic.get('change_pct', 'N/A')}%")
        print("="*60)

        if prediction:
            print(f"\n预测趋势: {prediction.get('trend_cn', 'N/A')}")
            print(f"概率: {prediction.get('probability', 0) * 100:.0f}%")
            print(f"目标价格区间: {prediction.get('target_price_low', 'N/A')} - {prediction.get('target_price_high', 'N/A')}")
            print(f"操作建议: {prediction.get('recommendation', 'N/A')}")

        # Save full result to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nFull result saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_select_short(args):
    """Short-term stock selection"""
    print(f"Running short-term stock selection (top {args.top_n})...")

    try:
        df = short_term_stock_selector(
            min_price=args.min_price,
            max_price=args.max_price,
            min_volume=args.min_volume,
            top_n=args.top_n
        )

        if df.empty:
            print("No stocks found matching criteria.")
            return 0

        # Print results
        print("\n" + "="*80)
        print(f"{'Rank':<6}{'Symbol':<10}{'Name':<20}{'Price':<12}{'Score':<10}{'Signals'}")
        print("="*80)

        for idx, row in df.iterrows():
            rank = idx + 1
            print(f"{rank:<6}{row['symbol']:<10}{row['name'][:18]:<20}"
                  f"{row['price']:<12.2f}{row['total_score']:<10}{row['signals'][:30]}")

        # Save to file if requested
        if args.output:
            df.to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"\nResults saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_select_long(args):
    """Long-term stock selection"""
    print(f"Running long-term stock selection (top {args.top_n})...")

    try:
        df = long_term_stock_selector(
            min_roe=args.min_roe,
            max_pe=args.max_pe,
            min_profit_growth=args.min_profit_growth,
            top_n=args.top_n
        )

        if df.empty:
            print("No stocks found matching criteria.")
            return 0

        # Print results
        print("\n" + "="*90)
        print(f"{'Rank':<6}{'Symbol':<10}{'Name':<16}{'Price':<10}{'PE':<8}{'ROE':<8}{'Score':<8}")
        print("="*90)

        for idx, row in df.iterrows():
            rank = idx + 1
            pe = f"{row['pe_ttm']:.2f}" if pd.notna(row.get('pe_ttm')) else 'N/A'
            roe = f"{row['roe']:.2f}%" if pd.notna(row.get('roe')) else 'N/A'
            print(f"{rank:<6}{row['symbol']:<10}{row['name'][:14]:<16}"
                  f"{row['price']:<10.2f}{pe:<8}{roe:<8}{row['total_score']:<8}")

        # Save to file if requested
        if args.output:
            df.to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"\nResults saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_alert_setup(args):
    """Setup stock alert"""
    print(f"Setting up alert for {args.symbol}...")

    try:
        # Parse condition
        condition = {}
        if ':' in args.condition:
            operator, value = args.condition.split(':')
            condition['operator'] = operator
            condition['value'] = float(value)

        alert_id = setup_alert(
            symbol=args.symbol,
            alert_type=args.type,
            condition=condition,
            notification_method=args.notify,
            expires_in_hours=args.expires
        )

        print(f"\nAlert setup successfully!")
        print(f"Alert ID: {alert_id}")
        print(f"Symbol: {args.symbol}")
        print(f"Type: {args.type}")
        print(f"Condition: {args.condition}")
        print(f"Notification: {args.notify}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Stock Analysis and Selection Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze a stock
    python stock_analyzer.py analyze 000001 --market sz

    # Short-term stock selection
    python stock_analyzer.py select-short --top-n 50

    # Long-term stock selection
    python stock_analyzer.py select-long --min-roe 15 --max-pe 30

    # Setup price alert
    python stock_analyzer.py alert-setup 000001 price "above:15.0"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a single stock')
    analyze_parser.add_argument('symbol', help='Stock symbol (e.g., 000001)')
    analyze_parser.add_argument('--market', default='sh', choices=['sh', 'sz', 'hk'],
                               help='Market type (default: sh)')
    analyze_parser.add_argument('--lookback', type=int, default=250,
                               help='Lookback days for analysis (default: 250)')
    analyze_parser.add_argument('--output', '-o', help='Output file path (JSON)')
    analyze_parser.set_defaults(func=cmd_analyze)

    # Select-short command
    select_short_parser = subparsers.add_parser('select-short', help='Short-term stock selection')
    select_short_parser.add_argument('--min-price', type=float, help='Minimum price filter')
    select_short_parser.add_argument('--max-price', type=float, help='Maximum price filter')
    select_short_parser.add_argument('--min-volume', type=int, help='Minimum volume filter')
    select_short_parser.add_argument('--top-n', type=int, default=50, help='Number of top stocks (default: 50)')
    select_short_parser.add_argument('--output', '-o', help='Output file path (CSV)')
    select_short_parser.set_defaults(func=cmd_select_short)

    # Select-long command
    select_long_parser = subparsers.add_parser('select-long', help='Long-term stock selection')
    select_long_parser.add_argument('--min-roe', type=float, default=15, help='Minimum ROE (default: 15)')
    select_long_parser.add_argument('--max-pe', type=float, default=30, help='Maximum PE (default: 30)')
    select_long_parser.add_argument('--min-profit-growth', type=float, default=20,
                                     help='Minimum profit growth (default: 20)')
    select_long_parser.add_argument('--top-n', type=int, default=30, help='Number of top stocks (default: 30)')
    select_long_parser.add_argument('--output', '-o', help='Output file path (CSV)')
    select_long_parser.set_defaults(func=cmd_select_long)

    # Alert-setup command
    alert_parser = subparsers.add_parser('alert-setup', help='Setup stock alert')
    alert_parser.add_argument('symbol', help='Stock symbol (e.g., 000001)')
    alert_parser.add_argument('type', choices=['price', 'volume', 'technical'],
                             help='Alert type')
    alert_parser.add_argument('condition', help='Condition string (e.g., "above:15.0")')
    alert_parser.add_argument('--notify', default='console',
                             choices=['console', 'email', 'wechat', 'dingtalk'],
                             help='Notification method (default: console)')
    alert_parser.add_argument('--expires', type=int, default=24,
                             help='Expiration time in hours (default: 24)')
    alert_parser.set_defaults(func=cmd_alert_setup)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
