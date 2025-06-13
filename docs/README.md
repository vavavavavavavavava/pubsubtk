# PubSubTk ドキュメント自動生成システム

## 🎯 概要

このシステムは、PubSubTkライブラリのドキュメントを自動生成します：

- **生成AI用リファレンス**: `REFERENCE_FULL.md`, `REFERENCE_SHORT.md`
- **MkDocs APIドキュメント**: 人間が読むための美しいドキュメントサイト
- **完全自動化**: ソースコード変更→一発コマンド→最新ドキュメント

## 🚀 クイックスタート

### 1. 初期セットアップ（一度だけ）

```bash
# 依存関係インストール
pip install -r requirements-dev.txt

# 初期ファイル生成
python scripts/generate_docs.py --init
```

### 2. ドキュメント生成（コード変更時）

```bash
# リファレンス生成 + MkDocsビルド + サーバー起動
python scripts/build_docs.py --serve
```

### 3. 本番デプロイ確認

```bash
# 本番用ビルド
python scripts/build_docs.py --build-prod

# 生成物確認
ls -la site/
```

## 📁 ファイル構成

```txt
docs/
├── README.md                    # このファイル
├── config.yml                   # 生成設定
├── templates/                   # テンプレートファイル
│   ├── common.md               # 共通部分
│   ├── full_suffix.md          # FULL版追加部分
│   └── short_suffix.md         # SHORT版追加部分
├── stylesheets/
│   └── extra.css               # MkDocs用カスタムCSS
├── gen_ref_pages.py            # MkDocs API生成スクリプト
├── REFERENCE_FULL.md           # AI用完全リファレンス（自動生成）
└── REFERENCE_SHORT.md          # AI用簡潔リファレンス（自動生成）

scripts/
├── generate_docs.py            # メイン生成スクリプト
├── build_docs.py               # 統合ビルドスクリプト
├── config.yml                  # 設定ファイル（テンプレート）
├── gen_ref_pages.py            # MkDocs生成スクリプト（テンプレート）
└── templates/                  # テンプレートファイル群
    ├── common.md
    ├── full_suffix.md
    └── short_suffix.md
```

## ⚙️ 設定のカスタマイズ

### `docs/config.yml` の編集

```yaml
# ソースコード構成の変更
source_code_sections:
  - name: "新しいセクション"
    files:
      - path: "src/pubsubtk/new_module.py"
        description: "新機能の説明"

# サンプルアプリの追加
sample_apps:
  - title: "新しいサンプルアプリ"
    path: "examples/new_app.py"
    description: "新しいサンプルの説明"
```

### テンプレートの編集

- `docs/templates/common.md`: 共通部分（概要、使い方など）
- `docs/templates/full_suffix.md`: FULL版のみに追加される部分
- `docs/templates/short_suffix.md`: SHORT版のみに追加される部分

## 🔧 コマンドリファレンス

### `scripts/generate_docs.py`

```bash
# 初期セットアップ
python scripts/generate_docs.py --init

# リファレンス生成
python scripts/generate_docs.py

# カスタム設定ファイル使用
python scripts/generate_docs.py --config my_config.yml

# 出力先指定
python scripts/generate_docs.py --full-output custom_full.md --short-output custom_short.md
```

### `scripts/build_docs.py`

```bash
# 開発用サーバー起動
python scripts/build_docs.py --serve

# 本番ビルド
python scripts/build_docs.py --build-prod

# リファレンス生成スキップ
python scripts/build_docs.py --skip-reference --serve

# 依存関係チェックスキップ
python scripts/build_docs.py --skip-deps-check --serve
```

## 🎨 カスタマイズ方法

### 1. 新しいソースファイルの追加

`docs/config.yml` の `source_code_sections` に追加：

```yaml
source_code_sections:
  - name: "新機能"
    files:
      - path: "src/pubsubtk/new_feature.py"
        description: "新機能の説明"
```

### 2. サンプルアプリの追加

`docs/config.yml` の `sample_apps` に追加：

```yaml
sample_apps:
  - title: "新しいサンプル"
    path: "examples/new_sample.py"
    description: "新しいサンプルの説明"
```

### 3. テンプレートの編集

- 共通部分の変更: `docs/templates/common.md`
- FULL版のみの変更: `docs/templates/full_suffix.md`
- SHORT版のみの変更: `docs/templates/short_suffix.md`

## 🤖 GitHub Actions

プロジェクトにpushすると自動的に：

1. リファレンス生成
2. MkDocsビルド
3. GitHub Pagesにデプロイ
4. 生成されたリファレンスをArtifactとして保存

### 手動デプロイ

```bash
# GitHub Pagesにデプロイ
mkdocs gh-deploy
```

## 🔍 トラブルシューティング

### よくある問題

1. **依存関係エラー**

   ```bash
   pip install -r requirements-dev.txt
   ```

2. **設定ファイルが見つからない**

   ```bash
   python scripts/generate_docs.py --init
   ```

3. **MkDocsビルドエラー**

   ```bash
   mkdocs build --strict
   ```

4. **テンプレートファイルが見つからない**

   ```bash
   # 初期セットアップを再実行
   python scripts/generate_docs.py --init
   ```

### デバッグ方法

```bash
# 詳細なエラー情報を表示
python scripts/build_docs.py --serve --skip-deps-check

# 段階的に実行
python scripts/generate_docs.py  # リファレンス生成
mkdocs build                     # MkDocsビルド
mkdocs serve                     # サーバー起動
```

## 📝 開発フロー

1. **ソースコード変更**

   ```bash
   vim src/pubsubtk/store/store.py
   ```

2. **ドキュメント更新**

   ```bash
   python scripts/build_docs.py --serve
   ```

3. **確認**
   - ブラウザで <http://127.0.0.1:8000> を開く
   - `docs/REFERENCE_FULL.md` を確認

4. **コミット**

   ```bash
   git add docs/REFERENCE_FULL.md docs/REFERENCE_SHORT.md
   git commit -m "docs: update API reference"
   git push
   ```

## 🎉 完成

これで、PubSubTkライブラリの完璧な自動ドキュメントシステムが完成です！

- **人間用**: 美しいMkDocsサイト
- **AI用**: 完全なリファレンスファイル
- **自動化**: GitHub Actions でデプロイ
- **保守性**: 設定ファイルでカスタマイズ可能
