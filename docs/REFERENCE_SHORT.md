# PubSubTk ライブラリ - AI リファレンスガイド(ショート版)

## 目次

* [概要](#概要)
* [コアコンセプト](#コアコンセプト)

  * [1. State管理](#1-state管理)
  * [2. PubSub通信](#2-pubsub通信)
  * [3. コンポーネントアーキテクチャ](#3-コンポーネントアーキテクチャ)
* [クイックスタート](#クイックスタート)
* [組み込みメソッドの使用（推奨）](#組み込みメソッドの使用推奨)
* [Stateパスの使用（推奨）](#stateパスの使用推奨)
* [コンポーネントライフサイクル](#コンポーネントライフサイクル)
* [Key Design Patterns](#key-design-patterns)

  * [1. State-Firstアーキテクチャ](#1-state-firstアーキテクチャ)
  * [2. アプリケーションセットアップパターン](#2-アプリケーションセットアップパターン)
  * [3. テンプレートコンポーネントパターン](#3-テンプレートコンポーネントパターン)
  * [4. Containerコンポーネントパターン](#4-containerコンポーネントパターン)
  * [5. Processorパターン](#5-processorパターン)
* [依存関係](#依存関係)

---

## 概要

PubSubTk は、Pydantic を用いた型安全な状態管理と Publish-Subscribe パターンを組み合わせ、Tkinter/ttk ベースの GUI アプリケーションを簡単に構築できる Python ライブラリです。

* **型安全な Store**: Pydantic モデルで状態を定義し、中央集権的に管理。
* **PubSub 通信**: トピック経由でコンポーネント間を疎結合に連携。
* **コンポーネント設計**: Container/Presentational/Template/Processor を使い分け、責務を明確化。

---

## コアコンセプト

### 1. State管理

* **Pydantic モデル** でアプリケーション状態を定義。
* Store クラスがモデルインスタンスを保持し、状態更新時に自動通知。
* **StateProxy** を介して `store.state.foo.bar` のようにパスベースでアクセスし、IDE 補完・型チェックを活用可能。

### 2. PubSub通信

* **DefaultUpdateTopic** や **DefaultNavigateTopic** といった組み込みトピックを利用。
* Container や Processor は `pub_update_state()`, `pub_switch_container()` などのメソッドを使ってメッセージ送信。
* 他コンポーネントは `sub_state_changed()` などで購読し、状態変化を検知して UI 更新を行う。

### 3. コンポーネントアーキテクチャ

* **Container Components**: Store に依存し、状態を読み書きして PubSub 経由でコンテンツを更新。
* **Presentational Components**: 受け取ったデータのみを描画し、状態管理の責務を持たない。
* **Template Components**: ヘッダー・メイン・サイドバーなどのレイアウトスロットを定義し、Container/Presentational を配置。
* **Processors**: ビジネスロジック処理専用。Store を経由して状態更新を行い、UI とは分離。

---

## クイックスタート

以下のシンプルな例を参照し、最小限の構成で PubSubTk を体験できます。

1. **状態モデルを定義**
   Pydantic を使ってアプリケーションの状態を表すモデルを作成します。

   ```python
   from pydantic import BaseModel
   from typing import List

   class TodoItem(BaseModel):
       id: int
       text: str
       completed: bool = False

   class AppState(BaseModel):
       todos: List[TodoItem] = []
       next_id: int = 1
   ```

2. **アプリケーションを作成**
   `TkApplication` を継承し、初期設定とコンテナ切り替えのロジックを追加します。

   ```python
   import pubsubtk

   class TodoApp(pubsubtk.TkApplication[AppState]):
       def __init__(self):
           super().__init__(AppState, title="Todo App", geometry="400x300")
       def setup_custom_logic(self):
           # 初期コンテナを起動
           self.pub_switch_container(TodoListContainer)
   ```

3. **Container を実装**
   Todo リストを追加・表示する Container を作成します。

   ```python
   import tkinter as tk
   from pubsubtk.ui.base.container_base import ContainerComponentTk

   class TodoListContainer(ContainerComponentTk[AppState]):
       def setup_ui(self):
           self.entry = tk.Entry(self)
           self.add_btn = tk.Button(self, text="追加", command=self.add_todo)
           self.listbox = tk.Listbox(self)
           self.entry.pack(fill=tk.X, padx=5, pady=5)
           self.add_btn.pack(pady=5)
           self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

       def setup_subscriptions(self):
           # "todos" が更新されたら on_todos_changed() を呼ぶ
           self.sub_state_changed(str(self.store.state.todos), self.on_todos_changed)

       def refresh_from_state(self):
           state = self.store.get_current_state()
           self.listbox.delete(0, tk.END)
           for todo in state.todos:
               mark = "✓" if todo.completed else "○"
               self.listbox.insert(tk.END, f"{mark} {todo.text}")

       def add_todo(self):
           text = self.entry.get().strip()
           if not text:
               return
           state = self.store.get_current_state()
           new_item = TodoItem(id=state.next_id, text=text)
           # リストに追加 & next_id を更新
           self.pub_add_to_list(str(self.store.state.todos), new_item)
           self.pub_update_state(str(self.store.state.next_id), state.next_id + 1)
           self.entry.delete(0, tk.END)

       def on_todos_changed(self, old_value, new_value):
           self.refresh_from_state()
   ```

4. **実行**

   ```python
   if __name__ == "__main__":
       app = TodoApp()
       app.setup_custom_logic()
       app.run()
   ```

これだけで、簡易的な Todo アプリが起動し、エントリに入力して「追加」ボタンを押すとリストに反映されます。

---

## 組み込みメソッドの使用（推奨）

PubSubTk では生のトピック文字列を使うより、以下の組み込みメソッドを使うほうが IDE 補完や型安全性が高まります。

```python
class SomeContainer(ContainerComponentTk[AppState]):
    def some_action(self):
        # 状態を更新
        self.pub_update_state(self.store.state.count, 42)
        # 他のコンテナへ切り替え
        self.pub_switch_container(OtherContainer)
        # サブウィンドウを開く
        self.pub_open_subwindow(DialogContainer, win_id="dialog1")
```

生の `publish("update_state", state_path="count", new_value=42)` のように書くと、IDE の補完が効かずミスの温床になります。

---

## Stateパスの使用（推奨）

* **StateProxy** を使うと、`str(self.store.state.foo.bar)` で自動的に文字列 "foo.bar" が得られます。
* IDE 補完で入力ミスを防ぎ、「Go to Definition」でモデル定義へジャンプ可能。

```python
# 推奨パターン
self.pub_update_state(self.store.state.user.name, "新しい名前")
self.sub_state_added(self.store.state.items, self.on_item_added)

# パスを文字列演算で扱いたいときは必ず str() を使う
path = str(self.store.state.user.email) + "_backup"

# 直接文字列で指定することも可能
self.pub_update_state("count", 100)
self.sub_state_changed("user.name", self.on_name_changed)
```

---

## コンポーネントライフサイクル

* **Container Components**

  1. コンストラクタで `store` を受け取る
  2. `setup_ui()` でウィジェットを構築
  3. `setup_subscriptions()` で PubSub 購読を設定
  4. `refresh_from_state()` で初期状態を反映
  5. `destroy()` 呼び出し時に自動的に `teardown()` で購読解除

* **Presentational Components**

  1. コンストラクタで UI を構築（`setup_ui()`）
  2. 外部から `update_data()` でデータを受け取り、画面描画のみ担う

* **Template Components**

  1. `define_slots()` で複数のレイアウト領域を定義
  2. `switch_slot_content(slot_name, Component, kwargs)` で任意のスロットにコンポーネントを配置

* **Processors**

  1. `setup_subscriptions()` でトピック購読を設定してビジネスロジックを実装
  2. `teardown()` で購読解除

---

## Key Design Patterns

### 1. State-Firstアーキテクチャ

* アプリの状態を最初に Pydantic モデルで定義し、Store が一元管理。
* UI は状態を参照・更新するだけで、状態そのものはコード全体で一貫性を保つ。

```python
from pydantic import BaseModel
from typing import List

class TodoItem(BaseModel):
    id: int
    text: str
    completed: bool = False

class AppState(BaseModel):
    todos: List[TodoItem] = []
    filter_mode: str = "all"
    next_id: int = 1
```

### 2. アプリケーションセットアップパターン

* `TkApplication` または `ThemedApplication` を継承し、初期ウィンドウ設定と PubSub の Mixin を組み合わせる。
* 起動時に `pub_registor_processor()` で必要な Processor を登録し、`pub_switch_container()` で最初の Container を表示。

```python
class MyApp(pubsubtk.TkApplication[AppState]):
    def __init__(self):
        super().__init__(AppState, title="My App", geometry="600x400")

    def setup_custom_logic(self):
        self.pub_registor_processor(MyProcessor)
        self.pub_switch_container(MainContainer)
```

### 3. テンプレートコンポーネントパターン

* 画面全体のレイアウト枠を定義し、ヘッダー・サイドバー・メイン・ステータスバーなどに分割。
* 各スロットには Container や Presentational を差し替えて配置。

```python
class AppTemplate(pubsubtk.TemplateComponentTtk[AppState]):
    def define_slots(self) -> dict[str, tk.Widget]:
        self.header = tk.Frame(self, height=50, bg="navy")
        self.header.pack(fill=tk.X)
        self.sidebar = tk.Frame(self, width=200, bg="gray")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.main = tk.Frame(self)
        self.main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.status = tk.Frame(self, height=30, bg="lightgray")
        self.status.pack(fill=tk.X)
        return {
            "header": self.header,
            "sidebar": self.sidebar,
            "main": self.main,
            "status": self.status,
        }
```

### 4. Containerコンポーネントパターン

* UI と状態更新ロジックを１つのクラスにまとめ、`setup_ui()`・`setup_subscriptions()`・`refresh_from_state()` を実装。
* ユーザー操作 → `pub_update_state()`／`pub_add_to_list()` → Store が更新 → `sub_state_changed()` で UI 更新、という流れ。

```python
class MainContainer(pubsubtk.ContainerComponentTk[AppState]):
    def setup_ui(self):
        self.btn = tk.Button(self, text="Increment", command=self.increment)
        self.btn.pack(pady=10)

    def setup_subscriptions(self):
        self.sub_state_changed(str(self.store.state.count), self.on_count_changed)

    def refresh_from_state(self):
        state = self.store.get_current_state()
        self.btn.config(text=f"Count: {state.count}")

    def increment(self):
        state = self.store.get_current_state()
        self.pub_update_state(str(self.store.state.count), state.count + 1)

    def on_count_changed(self, old, new):
        self.refresh_from_state()
```

### 5. Processorパターン

* ビジネスロジック専用のクラスを作成し、状態更新や他コンポーネントとの連携を担当。
* `setup_subscriptions()` でカスタムトピックを購読し、`pub_update_state()` などを呼び出す。

```python
class TodoProcessor(pubsubtk.ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe("todo.complete", self.complete_todo)

    def complete_todo(self, todo_id: int):
        state = self.store.get_current_state()
        updated = [
            item.copy(update={"completed": not item.completed}) 
            if item.id == todo_id else item
            for item in state.todos
        ]
        self.pub_update_state(str(self.store.state.todos), updated)
```

---

## 依存関係

* `pydantic`：状態モデルの定義とバリデーション
* `pypubsub`：内部の Publish-Subscribe 実装
* `ttkthemes`（任意）：ThemedTk を使う場合に必要
* `tkinter`：Python 標準の GUI フレームワーク

以上がショートバージョンとなります。必要に応じてクイックスタートの例をベースに各自のアプリ開発を開始してください。
