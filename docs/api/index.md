# APIリファレンス

PubSubTkライブラリの詳細なAPI仕様や活用パターンをまとめています。  
サイドバーから各クラス・モジュールの詳細ページへ移動できます。

---

## モジュール構成

PubSubTkは主に次のモジュール群で構成されています：

### Core

- **pubsubtk.core**  
  - [`PubSubBase`](pubsubtk/core/pubsub_base/) … PubSubの基底クラス
  - [`PubSubDefaultTopicBase`](pubsubtk/core/default_topic_base/) … デフォルトトピック用のユーティリティ

- **pubsubtk.store**  
  - [`Store`](pubsubtk/store/store/#pubsubtk.store.store.Store) … Pydanticベースの状態管理
  - [`StateProxy`](pubsubtk/store/store/#pubsubtk.store.store.StateProxy) … 型安全な状態アクセス

- **pubsubtk.topic**  
  - [`AutoNamedTopic`](pubsubtk/topic/topics/#pubsubtk.topic.topics.AutoNamedTopic) … 自動命名トピック
  - [`DefaultNavigateTopic`](pubsubtk/topic/topics/#pubsubtk.topic.topics.DefaultNavigateTopic)
  - [`DefaultUpdateTopic`](pubsubtk/topic/topics/#pubsubtk.topic.topics.DefaultUpdateTopic)
  - [`DefaultProcessorTopic`](pubsubtk/topic/topics/#pubsubtk.topic.topics.DefaultProcessorTopic)

### Application Framework

- **pubsubtk.app**  
  - [`TkApplication`](pubsubtk/app/application_base/#pubsubtk.app.application_base.TkApplication) … 標準Tkアプリ
  - [`ThemedApplication`](pubsubtk/app/application_base/#pubsubtk.app.application_base.ThemedApplication) … テーマ対応アプリ

- **pubsubtk.processor**  
  - [`ProcessorBase`](pubsubtk/processor/processor_base/) … ビジネスロジック基底クラス

### UI Components

- **pubsubtk.ui**  
  - [`ContainerComponentTk/Ttk`](pubsubtk/ui/base/container_base/#pubsubtk.ui.base.container_base.ContainerComponentTk)
  - [`PresentationalComponentTk/Ttk`](pubsubtk/ui/base/presentational_base/#pubsubtk.ui.base.presentational_base.PresentationalComponentTk)
  - [`TemplateComponentTk/Ttk`](pubsubtk/ui/base/template_base/#pubsubtk.ui.base.template_base.TemplateComponentTk)

### Utilities

- **pubsubtk.utils**  
  - [`make_async`](pubsubtk/utils/async_utils/#pubsubtk.utils.async_utils.make_async)
  - [`make_async_task`](pubsubtk/utils/async_utils/#pubsubtk.utils.async_utils.make_async_task)

---

## クイックナビゲーション

### よく使うクラス

| クラス | 用途 | リンク |
|--------|------|-------------|
| `TkApplication` | アプリケーション本体 | [pubsubtk.app](pubsubtk/app/) |
| `ContainerComponentTk` | 状態連携UI | [pubsubtk.ui](pubsubtk/ui/) |
| `PresentationalComponentTk` | 純粋表示UI | [pubsubtk.ui](pubsubtk/ui/) |
| `ProcessorBase` | ビジネスロジック | [pubsubtk.processor](pubsubtk/processor/) |
| `Store` | 状態管理 | [pubsubtk.store](pubsubtk/store/) |

### 主なメソッド

| メソッド | 説明 | 代表的な用途 |
|----------|------|----------|
| `pub_update_state()` | 状態を更新 | Container, Processor |
| `pub_switch_container()` | 画面切り替え | Container, Processor |
| `sub_state_changed()` | 状態変更監視 | Container |
| `setup_subscriptions()` | 購読設定 | Container, Processor |
| `refresh_from_state()` | UI更新 | Container |

---

## よくある使用パターン

### 状態管理の基本

```python
from pydantic import BaseModel
from pubsubtk import TkApplication, ContainerComponentTk

class AppState(BaseModel):
    counter: int = 0

class MainContainer(ContainerComponentTk[AppState]):
    def setup_ui(self): ...
    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.counter, self.on_counter_changed)
    def refresh_from_state(self): ...

app = TkApplication(AppState)
app.switch_container(MainContainer)
app.run()
```

### Processorの活用

```python
from pubsubtk import ProcessorBase

class MyProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe("custom.event", self.handle_event)
    def handle_event(self):
        self.pub_update_state(self.store.state.counter, 42)

# アプリ起動時にProcessor登録
app.pub_register_processor(MyProcessor)
```

### テンプレートの使い方

```python
from pubsubtk import TemplateComponentTk

class AppTemplate(TemplateComponentTk[AppState]):
    def define_slots(self):
        return {
            "header": self.header_frame,
            "main": self.main_frame,
        }

app.set_template(AppTemplate)
app.pub_switch_slot("main", MainContainer)
```

---

## 型安全・IDE支援

- **StateProxy**で型安全な状態更新・補完・定義ジャンプが可能
- ジェネリクスにより、各Store/Container/Processorで型が明示でき、ミス防止＆開発効率UP

---

## デバッグ・ユーティリティ

- `enable_pubsub_debug_logging()` でPubSubのメッセージ流れを確認可能
- 状態のスナップショットや復元もPydantic標準で手軽

---

## 命名規則

- **クラス名**: PascalCase（例: `MainContainer`）
- **メソッド名**: snake\_case（例: `setup_ui`）
- **トピック名**: UPPER\_CASE（例: `USER_LOGIN`）
- **状態フィールド**: snake\_case（例: `user_name`）

---

## 関連リンク

- [はじめに](../getting-started.md)
- [実装レシピ集](../cookbook.md)
- [サンプル集](../examples.md)
- [AIリファレンス](../ai-reference/REFERENCE_FULL.md)
  → ChatGPT・Copilot等でAIコーディングする際はこちらも活用ください
- [GitHub Repository](https://github.com/vavavavavavavavava/pubsubtk)

---

各APIの詳細は左の「API詳細」ナビゲーションからご覧ください。
