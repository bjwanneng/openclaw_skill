# 测试说明文档

## 目录结构

```
tests/
├── __init__.py              # 测试包初始化
├── README.md                # 本文件（测试说明）
├── conftest.py              # pytest 共享配置和 fixture
├── test_ak_market_tool.py   # ak_market_tool 工具测试
└── test_web_quote_validator.py  # web_quote_validator 工具测试
```

## 运行测试

### 前置条件

1. 确保已安装依赖：
```bash
pip install -e ".[dev]"
```

2. 确保已配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，设置 AKSHARE_DATA_PATH 等变量
```

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
# 测试 ak_market_tool
pytest tests/test_ak_market_tool.py

# 测试 web_quote_validator
pytest tests/test_web_quote_validator.py
```

### 运行特定测试函数

```bash
# 运行特定测试函数
pytest tests/test_ak_market_tool.py::test_realtime_quote

# 运行包含特定关键字的测试
pytest -k "realtime"
```

### 带覆盖率报告的测试

```bash
pytest --cov=openclaw_stock --cov-report=html --cov-report=term
```

### 调试模式测试

```bash
# 遇到错误时进入 PDB 调试
pytest --pdb

# 详细输出
pytest -v -s
```

## 测试分类

### 单元测试
- 测试单个函数或方法
- 使用 Mock 隔离外部依赖
- 快速执行

### 集成测试
- 测试多个组件的交互
- 可能调用真实的外部 API
- 需要网络连接

### 功能测试
- 测试完整的用户场景
- 端到端测试

## 标记说明

测试文件中使用以下 pytest 标记：

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.network`: 需要网络连接
- `@pytest.mark.slow`: 执行较慢的测试

运行特定标记的测试：

```bash
# 只运行单元测试
pytest -m unit

# 跳过网络测试
pytest -m "not network"

# 只运行集成测试且需要网络
pytest -m "integration and network"
```

## 编写新测试

参考现有测试文件的结构：

1. 导入必要的模块
2. 使用 `conftest.py` 中定义的 fixture
3. 编写测试函数，使用 `test_` 前缀
4. 使用断言验证结果

示例：

```python
def test_my_feature():
    """测试我的新功能"""
    # 准备数据
    input_data = {"symbol": "000001"}

    # 执行操作
    result = my_function(input_data)

    # 验证结果
    assert result["success"] is True
    assert result["data"]["name"] == "平安银行"
```

## 常见问题

### 1. 导入错误

**问题**: `ModuleNotFoundError: No module named 'openclaw_stock'`

**解决**: 确保已安装包：`pip install -e .`

### 2. 环境变量未加载

**问题**: `KeyError: 'AKSHARE_DATA_PATH'`

**解决**: 确保已创建 `.env` 文件并设置了必需的环境变量

### 3. 网络连接错误

**问题**: 测试连接外部 API 时超时

**解决**:
- 检查网络连接
- 检查是否需要代理（设置 `PROXY_URL`）
- 使用 `-m "not network"` 跳过网络测试

### 4. 测试执行很慢

**问题**: 运行所有测试需要很长时间

**解决**:
- 使用 `-m unit` 只运行单元测试
- 使用 `-x` 在遇到第一个错误时停止
- 使用 `--durations=10` 找出最慢的测试

## 持续集成

在 CI/CD 环境中运行测试：

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -e ".[dev]"
    - run: pytest --cov=openclaw_stock
```

## 获取帮助

- 查看 pytest 文档：https://docs.pytest.org/
- 项目 Issues：https://github.com/bjwanneng/openclaw-stock-research/issues
- 联系邮箱：bjzhangwn@gmail.com
