"""MkDocs APIリファレンス自動生成スクリプト"""

from pathlib import Path

import mkdocs_gen_files

# ソースコードのルートパス
src_root = Path("src")
nav_lines = []

# pubsubtkパッケージを走査
for path in sorted((src_root / "pubsubtk").rglob("*.py")):
    module_path = path.relative_to(src_root).with_suffix("")
    doc_path = path.relative_to(src_root).with_suffix(".md")
    full_doc_path = Path("api", doc_path)

    parts = tuple(module_path.parts)

    # __init__.pyは親モジュール名で表示
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = Path("api", doc_path)

    # 空のモジュールはスキップ
    if not parts:
        continue

    nav_lines.append(f"{'  ' * (len(parts) - 1)}* [{'.'.join(parts)}]({doc_path})")

    # ドキュメントページを生成
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        module_name = ".".join(parts)
        print(f"# {module_name}", file=fd)
        print(f"::: {module_name}", file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

# ナビゲーションファイルを生成
with mkdocs_gen_files.open("api/SUMMARY.md", "w") as nav_file:
    nav_file.writelines("\n".join(nav_lines))
