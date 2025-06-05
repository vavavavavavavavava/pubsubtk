# PubSubTk ライブラリ - AI リファレンスガイド(ショート版)

## 目次

- [PubSubTk ライブラリ - AI リファレンスガイド(ショート版)](#pubsubtk-ライブラリ---ai-リファレンスガイドショート版)
  - [目次](#目次)
  - [概要](#概要)
  - [コアコンセプト](#コアコンセプト)
    - [1. State管理](#1-state管理)
    - [2. PubSub通信](#2-pubsub通信)
    - [3. コンポーネントアーキテクチャ](#3-コンポーネントアーキテクチャ)
  - [クイックスタート](#クイックスタート)
  - [組み込みメソッドの使用（推奨）](#組み込みメソッドの使用推奨)
  - [Stateパスの使用（推奨）](#stateパスの使用推奨)
  - [コンポーネントライフサイクル](#コンポーネントライフサイクル)
  - [Key Design Patterns](#key-design-patterns)
    - [1. State-Firstアーキテクチャ](#1-state-firstアーキテクチャ)
    - [2. アプリケーションセットアップパターン](#2-アプリケーションセットアップパターン)
    - [3. テンプレートコンポーネントパターン](#3-テンプレートコンポーネントパターン)
    - [4. Containerコンポーネントパターン](#4-containerコンポーネントパターン)
    - [5. Processorパターン](#5-processorパターン)
  - [依存関係](#依存関係)

---

## 概要

PubSubTk は、Pydantic による型安全な状態管理と Publish-Subscribe パターンを組み合わせ、Tkinter/ttk ベースの GUI アプリケーションを手軽かつ堅牢に構築できる Python ライブラリです。

- **型安全な Store**: Pydantic モデルで状態を定義し、中央集権的に管理
- **PubSub 通信**: トピック経由でコンポーネント間を疎結合に連携
- **コンポーネント設計**: Container／Presentational／Template／Processor で責務分離

---

## コアコンセプト

### 1. State管理

- **Pydantic モデル**でアプリケーション状態を定義します。
- Store クラスがモデルインスタンスを保持し、状態更新時に自動通知を行います。
- **StateProxy** により `store.state.foo.bar` のようなパスアクセスが可能で、IDE 補完や型チェックを活用できます。

### 2. PubSub通信

- **DefaultUpdateTopic** や **DefaultNavigateTopic** などの組み込みトピックを利用できます。
- Container や Processor は `pub_update_state()` や `pub_switch_container()` などのメソッドでメッセージを送信します。
- 他のコンポーネントは `sub_state_changed()` などで購読し、状態変化を検知して UI を更新します。

### 3. コンポーネントアーキテクチャ

- **Container Components**: Store に依存し、状態を読み書きして PubSub 経由でコンテンツを更新
- **Presentational Components**: 受け取ったデータのみを描画し、状態管理の責務は持たない
- **Template Components**: レイアウトスロット（ヘッダー・メイン・サイドバーなど）を定義し、他コンポーネントを配置
- **Processors**: ビジネスロジック処理専用。Store を経由して状態を操作し、UI とは分離

---

## クイックスタート

1. **状態モデルの定義**
   Pydantic を使ってアプリケーション状態モデルを作成します。

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

2. **アプリケーションの作成**
   `TkApplication` を継承し、初期設定とメインコンテナの切り替えロジックを記述します。

   ```python
   from pubsubtk import TkApplication

   class TodoApp(TkApplication):
       def __init__(self):
           super().__init__(AppState, title="Todo App", geometry="400x300")

       def setup_custom_logic(self):
           self.pub_switch_container(TodoListContainer)
   ```

3. **Container の実装**
   Todo リストの追加・表示を行うコンテナを作成します。

   ```python
   import tkinter as tk
   from pubsubtk import ContainerComponentTk

   class TodoListContainer(ContainerComponentTk[AppState]):
       def setup_ui(self):
           self.entry = tk.Entry(self)
           self.add_btn = tk.Button(self, text="追加", command=self.add_todo)
           self.listbox = tk.Listbox(self)
           self.entry.pack(fill=tk.X, padx=5, pady=5)
           self.add_btn.pack(pady=5)
           self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

       def setup_subscriptions(self):
           self.sub_state_changed(self.store.state.todos, self.on_todos_changed)

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
           self.pub_add_to_list(self.store.state.todos, new_item)
           self.pub_update_state(self.store.state.next_id, state.next_id + 1)
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

---

## 組み込みメソッドの使用（推奨）

PubSubTk では生のトピック名を publish するのではなく、以下のような組み込みメソッドの利用を推奨します。
これにより IDE 補完・型安全性・保守性が大きく向上します。

```python
from pubsubtk import ContainerComponentTk

class SomeContainer(ContainerComponentTk[AppState]):
    def some_action(self):
        # 状態を更新
        self.pub_update_state(self.store.state.count, 42)
        # コンテナを切り替え
        self.pub_switch_container(OtherContainer)
        # サブウィンドウを開く
        self.pub_open_subwindow(DialogContainer, win_id="dialog1")
```

---

## Stateパスの使用（推奨）

- **StateProxy** を使うと `str(self.store.state.foo.bar)` で自動的に "foo.bar" が得られます。
- IDE 補完で入力ミスを防ぎ、「Go to Definition」でモデル定義へジャンプ可能です。

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

- **Container Components**

  1. コンストラクタで `store` を受け取る
  2. `setup_ui()` でウィジェットを構築
  3. `setup_subscriptions()` で PubSub 購読を設定
  4. `refresh_from_state()` で初期状態を反映
  5. `destroy()` 時に自動で購読解除

- **Presentational Components**

  1. コンストラクタで UI を構築（`setup_ui()`）
  2. 外部から `update_data()` でデータを受け取り描画のみ担当

- **Template Components**

  1. `define_slots()` で複数のレイアウト領域を定義
  2. `switch_slot_content(slot_name, Component, kwargs)` で任意のスロットにコンポーネントを配置

- **Processors**

  1. `setup_subscriptions()` でトピック購読を設定しビジネスロジックを実装
  2. `teardown()` で購読解除

---

## Key Design Patterns

### 1. State-Firstアーキテクチャ

アプリの状態を最初に Pydantic モデルで定義し、Store が一元管理します。UI は状態を参照・更新するだけで、状態そのものはコード全体で一貫性を保ちます。

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

---

### 2. アプリケーションセットアップパターン

`TkApplication` もしくは `ThemedApplication` を継承し、初期ウィンドウ設定や Processor 登録、最初の Container 表示などをまとめます。

```python
from pubsubtk import TkApplication

class MyApp(TkApplication):
    def __init__(self):
        super().__init__(AppState, title="My App", geometry="600x400")

    def setup_custom_logic(self):
        self.pub_registor_processor(MyProcessor)
        self.pub_switch_container(MainContainer)
```

---

### 3. テンプレートコンポーネントパターン

全体レイアウト枠を Template コンポーネントで定義し、スロットへコンポーネントを動的配置できます。

```python
import tkinter as tk
from pubsubtk import TemplateComponentTtk

class AppTemplate(TemplateComponentTtk[AppState]):
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

---

### 4. Containerコンポーネントパターン

UI と状態更新ロジックを１つのクラスにまとめ、`setup_ui()`・`setup_subscriptions()`・`refresh_from_state()` を実装します。

```python
import tkinter as tk
from pubsubtk import ContainerComponentTk

class MainContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        self.btn = tk.Button(self, text="Increment", command=self.increment)
        self.btn.pack(pady=10)

    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.count, self.on_count_changed)

    def refresh_from_state(self):
        state = self.store.get_current_state()
        self.btn.config(text=f"Count: {state.count}")

    def increment(self):
        state = self.store.get_current_state()
        self.pub_update_state(self.store.state.count, state.count + 1)

    def on_count_changed(self, old, new):
        self.refresh_from_state()
```

---

### 5. Processorパターン

ビジネスロジック専用の Processor を作成し、状態操作や他コンポーネント連携を担います。

```python
from pubsubtk import ProcessorBase

class TodoProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe("todo.complete", self.complete_todo)

    def complete_todo(self, todo_id: int):
        state = self.store.get_current_state()
        updated = [
            item.copy(update={"completed": not item.completed}) 
            if item.id == todo_id else item
            for item in state.todos
        ]
        self.pub_update_state(self.store.state.todos, updated)
```

---

## 依存関係

- `pydantic`: 状態モデルの定義とバリデーション
- `pypubsub`: 内部の Publish-Subscribe 実装
- `ttkthemes`（任意）: ThemedTk を使う場合に必要
- `tkinter`: Python 標準の GUI フレームワーク
