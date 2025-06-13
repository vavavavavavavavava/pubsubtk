"""MkDocs APIリファレンス自動生成スクリプト"""

from pathlib import Path

import mkdocs_gen_files

# ソースコードのルートパス
src_root = Path("src")
nav_lines = ["# API Reference", ""]

# pubsubtkパッケージを走査
for path in sorted((src_root / "pubsubtk").rglob("*.py")):
    # __init__.pyは完全スキップ
    if path.name == "__init__.py":
        continue

    module_path = path.relative_to(src_root).with_suffix("")
    doc_path = path.relative_to(src_root).with_suffix(".md")
    full_doc_path = Path("api", doc_path)

    parts = tuple(module_path.parts)

    # 空のモジュールはスキップ
    if not parts:
        continue

    # 適切な相対パスでナビゲーション生成
    indent = "  " * (len(parts) - 1)
    module_name = ".".join(parts)
    nav_lines.append(f"{indent}* [{module_name}]({doc_path})")

    # ドキュメントページを生成
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        print(f"# {module_name}", file=fd)
        print("", file=fd)
        print(f"::: {module_name}", file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)
