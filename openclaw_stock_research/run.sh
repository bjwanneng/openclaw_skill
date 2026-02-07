#!/bin/bash
# OpenClaw Stock Research - 自动激活虚拟环境的运行脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查虚拟环境是否存在
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "错误: 虚拟环境不存在，请先运行: python -m venv venv"
    exit 1
fi

# 激活虚拟环境
source "$SCRIPT_DIR/venv/bin/activate"

# 检查是否安装了项目
if ! python -c "import openclaw_stock" 2>/dev/null; then
    echo "提示: 项目未安装，正在安装..."
    pip install -e "$SCRIPT_DIR"
fi

# 根据参数执行不同命令
case "${1:-}" in
    "test"|"tests")
        shift
        echo "运行测试..."
        pytest "$SCRIPT_DIR/tests/" "$@"
        ;;
    "analyze")
        shift
        echo "运行个股分析..."
        python "$SCRIPT_DIR/scripts/stock_analyzer.py" analyze "$@"
        ;;
    "select-short")
        shift
        echo "运行短期选股..."
        python "$SCRIPT_DIR/scripts/stock_analyzer.py" select-short "$@"
        ;;
    "shell"|"python")
        shift
        echo "进入 Python Shell..."
        python "$@"
        ;;
    "pip")
        shift
        pip "$@"
        ;;
    "")
        echo "OpenClaw Stock Research - 使用帮助"
        echo ""
        echo "用法: ./run.sh <命令> [参数]"
        echo ""
        echo "可用命令:"
        echo "  test              运行所有测试"
        echo "  analyze <股票代码> 分析个股"
        echo "  select-short      短期选股"
        echo "  shell             进入 Python Shell"
        echo "  pip               运行 pip 命令"
        echo ""
        echo "示例:"
        echo "  ./run.sh test -v                    # 详细模式运行测试"
        echo "  ./run.sh analyze 000001 --market sz # 分析平安银行"
        ;;
    *)
        # 直接传递参数给 Python
        python "$@"
        ;;
esac
