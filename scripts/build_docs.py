#!/usr/bin/env python3
"""
ドキュメント統合ビルドスクリプト

使用方法:
    python scripts/build_docs.py [--serve] [--build-prod] [--skip-reference]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str, ignore_errors: bool = False):
    """コマンド実行"""
    print(f"🔨 {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ エラー: {description}")
        print(f"コマンド: {' '.join(cmd)}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        if not ignore_errors:
            sys.exit(1)
    else:
        print(f"✅ {description} 完了")
        if result.stdout.strip():
            print(f"出力: {result.stdout.strip()}")


def check_dependencies():
    """必要な依存関係をチェック"""
    required_packages = [
        "mkdocs",
        "mkdocs-material",
        "mkdocstrings[python]",
        "mkdocs-gen-files",
        "mkdocs-literate-nav",
        "pyyaml",
    ]

    print("📦 依存関係チェック中...")

    missing_packages = []
    for package in required_packages:
        try:
            pkg_name = package.split("[")[0]  # mkdocstrings[python] -> mkdocstrings
            __import__(pkg_name.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ 以下のパッケージが不足しています:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\n以下のコマンドでインストールしてください:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)

    print("✅ 依存関係OK")


def main():
    parser = argparse.ArgumentParser(description="ドキュメント統合ビルド")
    parser.add_argument("--serve", action="store_true", help="ビルド後にサーバー起動")
    parser.add_argument("--build-prod", action="store_true", help="本番用ビルド")
    parser.add_argument(
        "--skip-reference", action="store_true", help="リファレンス生成をスキップ"
    )
    parser.add_argument(
        "--skip-deps-check", action="store_true", help="依存関係チェックをスキップ"
    )

    args = parser.parse_args()

    # 作業ディレクトリをプロジェクトルートに移動
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print(f"📁 作業ディレクトリ: {project_root}")

    # 依存関係チェック
    if not args.skip_deps_check:
        check_dependencies()

    # 1. リファレンス生成
    if not args.skip_reference:
        run_command(
            [sys.executable, "scripts/generate_docs.py"], "生成AI用リファレンス作成"
        )

    # 2. MkDocs操作
    if args.build_prod:
        run_command(["mkdocs", "build", "--strict"], "MkDocs本番ビルド")
        print("📦 本番ビルド完了! site/ フォルダを確認してください")

    elif args.serve:
        print("🚀 MkDocsサーバーを起動中...")
        print("   http://127.0.0.1:8000 でアクセスできます")
        print("   Ctrl+C で停止")
        try:
            subprocess.run(["mkdocs", "serve"])
        except KeyboardInterrupt:
            print("\n🛑 サーバーを停止しました")

    else:
        print("✅ ドキュメント更新完了")
        print("💡 次のコマンドでプレビューできます:")
        print("   python scripts/build_docs.py --serve")


if __name__ == "__main__":
    main()
