# storybook/auto_discover.py
"""AST 解析で @story を含むモジュールだけ import するユーティリティ."""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable, List


def _contains_story_decorator(py_file: Path) -> bool:
    """.py ファイルに `@story` デコレータがあるか静的解析で判定する。

    Args:
        py_file: 対象の Python ファイルパス
    Returns:
        True なら story デコレータが登場する
    """
    try:
        source = py_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    try:
        tree = ast.parse(source, filename=str(py_file))
    except SyntaxError:
        # 不完全なファイルはスキップ
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for deco in node.decorator_list:
                # @story(...)
                if isinstance(deco, ast.Call):
                    name = getattr(deco.func, "id", None) or getattr(
                        deco.func, "attr", None
                    )
                # @story  (引数なし)
                elif isinstance(deco, ast.Name):
                    name = deco.id
                # @sb.story など
                elif isinstance(deco, ast.Attribute):
                    name = deco.attr
                else:
                    name = None

                if name == "story":
                    return True
    return False


def _to_module_name(py_file: Path, src_root: Path) -> str:
    """src_root からの相対パスを dotted モジュール名に変換。"""
    rel = py_file.relative_to(src_root).with_suffix("")  # strip '.py'
    return ".".join(rel.parts)


def discover_stories(src_dir: str | Path = "src") -> List[ModuleType]:
    """src_dir 以下で `@story` を含むファイルだけ import して登録を走らせる。

    Args:
        src_dir: プロジェクトのソースディレクトリ
    Returns:
        実際に import されたモジュールオブジェクトのリスト
    """
    src_root = Path(src_dir).resolve()
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    imported: List[ModuleType] = []
    py_files: Iterable[Path] = src_root.rglob("*.py")

    for py_file in py_files:
        # 無視したいパスはここで continue
        if any(part in ("tests", "__pycache__", ".venv") for part in py_file.parts):
            continue
        if not _contains_story_decorator(py_file):
            continue

        module_name = _to_module_name(py_file, src_root)
        try:
            mod = importlib.import_module(module_name)
            imported.append(mod)
        except Exception as exc:
            print(f"[Storybook] Import error: {module_name} -> {exc}")

    return imported
