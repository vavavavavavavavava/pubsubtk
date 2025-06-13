"""
PubSubTk ドキュメント自動生成スクリプト

使用方法:
    python scripts/generate_docs.py --init      # 初期セットアップ
    python scripts/generate_docs.py             # ドキュメント生成
"""

import argparse
import shutil
from pathlib import Path
from typing import List, Tuple

import yaml


class DocumentConfig:
    """ドキュメント生成設定管理"""

    def __init__(self, config_path: Path):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    @property
    def source_files(self) -> List[Tuple[str, str, str]]:
        """(section_name, file_path, description)のリストを返す"""
        result = []
        for section in self.config["source_code_sections"]:
            section_name = section["name"]
            for file_info in section["files"]:
                result.append(
                    (section_name, file_info["path"], file_info.get("description", ""))
                )
        return result

    @property
    def sample_apps(self) -> List[Tuple[str, str, str]]:
        """(title, file_path, description)のリストを返す"""
        return [
            (app["title"], app["path"], app.get("description", ""))
            for app in self.config.get("sample_apps", [])
        ]

    @property
    def common_template(self) -> str:
        return self.config["templates"]["common"]

    @property
    def full_template(self) -> str:
        return self.config["templates"]["full"]

    @property
    def short_template(self) -> str:
        return self.config["templates"]["short"]


class ReferenceGenerator:
    """リファレンス生成器"""

    def __init__(self, config: DocumentConfig, project_root: Path):
        self.config = config
        self.project_root = project_root

    def read_file_safe(self, file_path: Path) -> str:
        """ファイルを安全に読み込み"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"# エラー: ファイル読み込みに失敗\n# {e}\n"

    def generate_source_code_section(self) -> str:
        """ソースコードセクションを生成"""
        content = []
        current_section = None

        for section_name, file_path, description in self.config.source_files:
            # セクション見出し
            if section_name != current_section:
                content.extend([f"### {section_name}", ""])
                current_section = section_name

            # ファイル見出し
            full_path = self.project_root / file_path
            content.append(f"#### `{file_path}`")
            content.append("")

            if description:
                content.append(description)
                content.append("")

            # ファイル内容
            file_content = self.read_file_safe(full_path)
            content.extend(["```python", file_content.rstrip(), "```", ""])

        return "\n".join(content)

    def generate_sample_apps_section(self) -> str:
        """サンプルアプリセクションを生成"""
        content = []

        for title, file_path, description in self.config.sample_apps:
            content.append(f"### {title}")
            content.append("")

            if description:
                content.append(description)
                content.append("")

            full_path = self.project_root / file_path
            file_content = self.read_file_safe(full_path)

            content.extend(["```python", file_content.rstrip(), "```", ""])

        return "\n".join(content)

    def process_template(self, template_content: str) -> str:
        """テンプレート内のプレースホルダーを処理"""

        # {{SAMPLE_APPS}} を置換
        if "{{SAMPLE_APPS}}" in template_content:
            sample_section = self.generate_sample_apps_section()
            template_content = template_content.replace(
                "{{SAMPLE_APPS}}", sample_section
            )

        # {{SOURCE_CODE}} を置換
        if "{{SOURCE_CODE}}" in template_content:
            source_section = self.generate_source_code_section()
            template_content = template_content.replace(
                "{{SOURCE_CODE}}", source_section
            )

        return template_content

    def generate_reference(self, template_type: str, output_path: Path):
        """指定タイプのリファレンスを生成"""

        # 共通テンプレート読み込み
        common_template_path = self.project_root / self.config.common_template
        common_content = self.read_file_safe(common_template_path)

        # タイプ別テンプレート読み込み
        if template_type == "full":
            type_template_path = self.project_root / self.config.full_template
        elif template_type == "short":
            type_template_path = self.project_root / self.config.short_template
        else:
            raise ValueError(f"Unknown template type: {template_type}")

        type_content = self.read_file_safe(type_template_path)

        # テンプレート結合
        full_template = common_content + "\n" + type_content

        # プレースホルダー処理
        final_content = self.process_template(full_template)

        # 出力
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        print(f"✅ {template_type.upper()} リファレンス生成: {output_path}")


def copy_template_files(project_root: Path):
    """テンプレートファイルをコピー"""

    # スクリプトと同じディレクトリにあるテンプレートファイルを探す
    script_dir = Path(__file__).parent
    template_source_dir = script_dir / "templates"

    if not template_source_dir.exists():
        # フォールバック: プロジェクトルートからの相対パス
        template_source_dir = project_root / "scripts" / "templates"

    target_dir = project_root / "docs" / "templates"
    target_dir.mkdir(parents=True, exist_ok=True)

    template_files = ["common.md", "full_suffix.md", "short_suffix.md"]

    for template_file in template_files:
        source_file = template_source_dir / template_file
        target_file = target_dir / template_file

        if source_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"✅ テンプレートコピー: {target_file}")
        else:
            print(f"⚠️  テンプレートファイルが見つかりません: {source_file}")


def copy_initial_files(project_root: Path):
    """初期ファイルをコピー"""

    script_dir = Path(__file__).parent

    # config.yml のコピー
    config_source = script_dir / "config.yml"
    config_target = project_root / "docs" / "config.yml"

    if config_source.exists():
        config_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_source, config_target)
        print(f"✅ 設定ファイルコピー: {config_target}")

    # MkDocs API生成スクリプトのコピー
    gen_source = script_dir / "gen_ref_pages.py"
    gen_target = project_root / "docs" / "gen_ref_pages.py"

    if gen_source.exists():
        gen_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gen_source, gen_target)
        print(f"✅ MkDocs生成スクリプトコピー: {gen_target}")


def main():
    parser = argparse.ArgumentParser(description="PubSubTk ドキュメント生成")
    parser.add_argument("--init", action="store_true", help="初期セットアップ")
    parser.add_argument("--config", default="scripts/config.yml", help="設定ファイル")
    parser.add_argument(
        "--full-output", default="docs/REFERENCE_FULL.md", help="FULL版出力先"
    )
    parser.add_argument(
        "--short-output", default="docs/REFERENCE_SHORT.md", help="SHORT版出力先"
    )

    args = parser.parse_args()

    project_root = Path.cwd()

    # 初期セットアップ
    if args.init:
        print("🚀 初期セットアップを実行中...")
        copy_initial_files(project_root)
        copy_template_files(project_root)
        print("✅ 初期セットアップ完了!")
        print(f"📝 設定ファイルを確認してください: {args.config}")
        return

    # 設定ファイル確認
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ 設定ファイルが見つかりません: {config_path}")
        print("💡 --init で初期セットアップを実行してください")
        return

    # ドキュメント生成
    print("📖 ドキュメント生成中...")
    config = DocumentConfig(config_path)
    generator = ReferenceGenerator(config, project_root)

    # FULL版生成
    generator.generate_reference("full", Path(args.full_output))

    # SHORT版生成
    generator.generate_reference("short", Path(args.short_output))

    print("🎉 ドキュメント生成完了!")


if __name__ == "__main__":
    main()
