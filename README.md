# PubSubTk

**PubSubTk** は、イベント駆動＆状態管理型の Python GUIアプリケーションを、型安全かつ疎結合で構築できる軽量ライブラリです。

**プロジェクトサイト:** [https://vavavavavavavavava.github.io/pubsubtk/](https://vavavavavavavavava.github.io/pubsubtk/)

主な特徴：

* **UIとビジネスロジックの疎結合** ― Publish/Subscribe（Pub/Sub）で部品間を非同期メッセージ連携
* **Pydanticモデル** による型安全な状態管理。バリデーションや JSON Schema 出力も簡単
* **Container / Presentational / Processor** 3層分離パターンを標準化（Reactスタイルの設計をTkinterでも）
* **Pub/Subによる画面遷移・サブウィンドウ管理**と**リアクティブUI更新**をサポート
* 依存は純正Pythonのみ（`tkinter`, `pypubsub`, `pydantic`）。Tkテーマ変更用に `ttkthemes` も利用可能

---

## 📦 インストール

```bash
pip install git+https://github.com/vavavavavavavavava/pubsubtk
```

**要件:**

| パッケージ     | 最低バージョン | 備考             |
| --------- | ------- | -------------- |
| Python    | 3.11    | スレッドセーフTkが使える版 |
| pypubsub  | 4.0     | Python 3 専用    |
| pydantic  | 2.x     | 型安全＆高速         |
| ttkthemes | 任意      | テーマ適用の場合のみ     |

---

## 📖 リファレンス

* [フルリファレンス（REFERENCE_FULL.md）](docs/REFERENCE_FULL.md)
  └ 全コードと設計解説の完全版。
* [ショートリファレンス（REFERENCE_SHORT.md）](docs/REFERENCE_SHORT.md)
  └ フルリファレンスからソースコードを除外した圧縮版

**ChatGPT等でコード生成や設計相談をする際は、上記リファレンスを提示するとAIの理解度＆出力精度が大幅UPします！**

---

## 🙌 貢献・フィードバック

* Issue / PR は GitHub で歓迎！
  [https://github.com/vavavavavavavavava/pubsubtk](https://github.com/vavavavavavavavava/pubsubtk)
* ドキュメント改善案やユースケース紹介もお気軽にどうぞ！

---

ご要望やカスタマイズ相談は Issue まで！
