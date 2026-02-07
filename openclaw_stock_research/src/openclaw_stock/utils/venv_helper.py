"""
虚拟环境自动激活助手

提供自动检测和激活虚拟环境的功能，确保工具在正确的 Python 环境中运行。
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


def find_venv_path(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    从给定路径开始向上查找虚拟环境

    查找顺序：
    1. 当前目录下的 venv/ 或 .venv/
    2. 项目根目录下的 venv/ 或 .venv/
    3. 环境变量 VIRTUAL_ENV 指定的路径

    Args:
        start_path: 开始查找的路径，默认为当前文件所在目录

    Returns:
        虚拟环境的路径，如果未找到则返回 None
    """
    if start_path is None:
        start_path = Path(__file__).resolve().parent

    # 1. 检查当前目录及上级目录的 venv 或 .venv
    current = start_path
    for _ in range(5):  # 向上查找最多5层
        for venv_name in ['venv', '.venv', 'env']:
            venv_path = current / venv_name
            if venv_path.exists() and (venv_path / 'bin' / 'python').exists():
                return venv_path
        # 向上查找
        parent = current.parent
        if parent == current:  # 到达根目录
            break
        current = parent

    # 2. 检查环境变量
    virtual_env = os.environ.get('VIRTUAL_ENV')
    if virtual_env:
        venv_path = Path(virtual_env)
        if venv_path.exists():
            return venv_path

    # 3. 检查 common 位置
    common_paths = [
        Path.home() / '.openclaw' / 'venv',
        Path.home() / '.venvs' / 'openclaw',
        Path('/opt/openclaw/venv'),
    ]
    for path in common_paths:
        if path.exists() and (path / 'bin' / 'python').exists():
            return path

    return None


def activate_venv(venv_path: Path) -> bool:
    """
    激活虚拟环境

    通过修改 sys.path 和 os.environ 来激活虚拟环境，无需重新启动 Python 进程。

    Args:
        venv_path: 虚拟环境的路径

    Returns:
        是否成功激活
    """
    if not venv_path.exists():
        print(f"[VenvHelper] 虚拟环境不存在: {venv_path}")
        return False

    python_path = venv_path / 'bin' / 'python'
    if not python_path.exists():
        print(f"[VenvHelper] 虚拟环境的 Python 解释器不存在: {python_path}")
        return False

    # 检查是否已经激活
    current_executable = Path(sys.executable).resolve()
    target_executable = python_path.resolve()
    if current_executable == target_executable:
        print(f"[VenvHelper] 已经在目标虚拟环境中运行")
        return True

    # 获取虚拟环境的 site-packages 路径
    site_packages = None
    for sp in venv_path.glob('lib/python*/site-packages'):
        if sp.is_dir():
            site_packages = sp
            break

    if not site_packages:
        print(f"[VenvHelper] 无法找到 site-packages 目录")
        return False

    # 修改 sys.path，将虚拟环境的 site-packages 添加到最前面
    if str(site_packages) not in sys.path:
        sys.path.insert(0, str(site_packages))
        print(f"[VenvHelper] 已添加 site-packages 到 sys.path: {site_packages}")

    # 修改环境变量
    os.environ['VIRTUAL_ENV'] = str(venv_path)
    os.environ['PATH'] = f"{venv_path / 'bin'}:{os.environ.get('PATH', '')}"

    # 修改 sys.executable 指向虚拟环境的 Python
    sys.executable = str(python_path)

    print(f"[VenvHelper] 虚拟环境已激活: {venv_path}")
    return True


def auto_activate() -> bool:
    """
    自动查找并激活虚拟环境

    这是主要的入口函数，在工具脚本开头调用即可自动激活正确的虚拟环境。

    Returns:
        是否成功激活（如果找不到虚拟环境或已经激活，也返回 True）

    Example:
        >>> from openclaw_stock.utils.venv_helper import auto_activate
        >>> auto_activate()  # 放在脚本开头
        >>> # 后续代码在正确的虚拟环境中运行
    """
    # 检查是否已经在虚拟环境中
    if hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        # 已经在虚拟环境中
        venv_path = Path(sys.prefix)
        print(f"[VenvHelper] 当前已在虚拟环境中: {venv_path}")
        return True

    # 查找虚拟环境
    venv_path = find_venv_path()
    if not venv_path:
        print("[VenvHelper] 未找到虚拟环境，将使用当前 Python 环境")
        print("[VenvHelper] 提示: 如果工具运行异常，请确保已创建虚拟环境并安装依赖")
        return True  # 返回 True，让调用者决定是否继续

    # 激活虚拟环境
    return activate_venv(venv_path)


# 向后兼容的别名
ensure_venv = auto_activate
