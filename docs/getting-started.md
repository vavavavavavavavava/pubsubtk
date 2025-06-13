# Getting Started

PubSubTkを使って、型安全で疎結合なGUIアプリケーション開発を始めましょう！

## 📦 インストール

### GitHubから直接インストール

```bash
pip install git+https://github.com/vavavavavavavavava/pubsubtk
```

### 開発版（推奨）

```bash
git clone https://github.com/vavavavavavavavava/pubsubtk.git
cd pubsubtk
pip install -e .
```

### 要件確認

- **Python**: 3.11以上
- **依存関係**: `tkinter`（標準ライブラリ）、`pypubsub`、`pydantic`、`ttkthemes`（オプション）

## 🎯 基本概念

PubSubTkは3つの主要コンポーネントで構成されています：

### 1. Store（状態管理）

Pydanticモデルでアプリケーションの状態を定義します。

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
    filter_mode: str = "all"  # "all", "active", "completed"
```

### 2. Container（状態連携UI）

状態を監視し、UIを更新するスマートコンポーネントです。

```python
from pubsubtk import ContainerComponentTk

class TodoListContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        """UI構築"""
        # ウィジェットを作成・配置
        
    def setup_subscriptions(self):
        """状態変更の監視設定"""
        self.sub_state_changed(self.store.state.todos, self.on_todos_changed)
        
    def refresh_from_state(self):
        """状態からUIを更新"""
        state = self.store.get_current_state()
        # UIに状態を反映
```

### 3. Presentational（純粋表示）

データを受け取って表示するだけのダムコンポーネントです。

```python
from pubsubtk import PresentationalComponentTk

class TodoItemView(PresentationalComponentTk):
    def setup_ui(self):
        """UI構築"""
        self.checkbox = tk.Checkbutton(self, command=self.on_toggle)
        self.label = tk.Label(self)
        
    def update_data(self, todo_item: TodoItem):
        """データ更新"""
        self.checkbox.set(todo_item.completed)
        self.label.config(text=todo_item.text)
        
    def on_toggle(self):
        """イベント発火"""
        self.trigger_event("toggle", todo_id=self.todo_item.id)
```

## 🚀 ステップバイステップ チュートリアル

### Step 1: シンプルなカウンターアプリ

まず、基本的なカウンターアプリを作成してみましょう。

```python
from pydantic import BaseModel
from pubsubtk import TkApplication, ContainerComponentTk
import tkinter as tk

# 1. 状態定義
class CounterState(BaseModel):
    count: int = 0

# 2. UIコンポーネント
class CounterContainer(ContainerComponentTk[CounterState]):
    def setup_ui(self):
        # カウンター表示
        self.count_label = tk.Label(self, text="0", font=("Arial", 32))
        self.count_label.pack(pady=20)
        
        # ボタン
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="-", command=self.decrement).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="+", command=self.increment).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
    
    def setup_subscriptions(self):
        # カウンター変更を監視
        self.sub_state_changed(self.store.state.count, self.on_count_changed)
    
    def refresh_from_state(self):
        state = self.store.get_current_state()
        self.count_label.config(text=str(state.count))
    
    def on_count_changed(self, old_value, new_value):
        self.count_label.config(text=str(new_value))
    
    def increment(self):
        state = self.store.get_current_state()  
        self.pub_update_state(self.store.state.count, state.count + 1)
    
    def decrement(self):
        state = self.store.get_current_state()
        self.pub_update_state(self.store.state.count, state.count - 1)
    
    def reset(self):
        self.pub_update_state(self.store.state.count, 0)

# 3. アプリケーション起動
if __name__ == "__main__":
    app = TkApplication(CounterState, title="Counter App")
    app.switch_container(CounterContainer)
    app.run()
```

### Step 2: Processorによるビジネスロジック分離

複雑なロジックはProcessorに分離します。

```python
from pubsubtk import ProcessorBase, AutoNamedTopic
from enum import auto

# カスタムイベント定義
class CounterEvents(AutoNamedTopic):
    INCREMENT = auto()
    DECREMENT = auto() 
    RESET = auto()

class CounterProcessor(ProcessorBase[CounterState]):
    def setup_subscriptions(self):
        self.subscribe(CounterEvents.INCREMENT, self.handle_increment)
        self.subscribe(CounterEvents.DECREMENT, self.handle_decrement)
        self.subscribe(CounterEvents.RESET, self.handle_reset)
    
    def handle_increment(self):
        state = self.store.get_current_state()
        new_count = state.count + 1
        self.pub_update_state(self.store.state.count, new_count)
        
        # ビジネスルール: 10の倍数で特別処理
        if new_count % 10 == 0:
            print(f"🎉 {new_count} に到達！")
    
    def handle_decrement(self):
        state = self.store.get_current_state()
        # ビジネスルール: 負の数にはしない
        new_count = max(0, state.count - 1)
        self.pub_update_state(self.store.state.count, new_count)
    
    def handle_reset(self):
        self.pub_update_state(self.store.state.count, 0)

# Containerから直接状態変更する代わりにイベント発行
class CounterContainer(ContainerComponentTk[CounterState]):
    # ... setup_ui, setup_subscriptions, refresh_from_state は同じ ...
    
    def increment(self):
        self.publish(CounterEvents.INCREMENT)
    
    def decrement(self):
        self.publish(CounterEvents.DECREMENT)
    
    def reset(self):
        self.publish(CounterEvents.RESET)

# アプリケーション起動時にProcessorを登録
if __name__ == "__main__":
    app = TkApplication(CounterState, title="Counter App with Processor")
    app.pub_register_processor(CounterProcessor)  # Processor登録
    app.switch_container(CounterContainer)
    app.run()
```

### Step 3: 複数画面の管理

テンプレートを使用した複数画面アプリケーション。

```python
from pubsubtk import TemplateComponentTk

class AppTemplate(TemplateComponentTk[CounterState]):
    def define_slots(self):
        # ヘッダー
        header = tk.Frame(self, height=60, bg="navy")
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # メインコンテンツ
        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)
        
        return {
            "header": header,
            "main": main,
        }

class HeaderContainer(ContainerComponentTk[CounterState]):
    def setup_ui(self):
        self.configure(bg="navy")
        
        tk.Label(self, text="Counter App", fg="white", bg="navy", 
                font=("Arial", 16, "bold")).pack(side=tk.LEFT, padx=10, pady=10)
        
        # 画面切り替えボタン
        nav_frame = tk.Frame(self, bg="navy")
        nav_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Button(nav_frame, text="Counter", 
                 command=self.show_counter).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="Settings", 
                 command=self.show_settings).pack(side=tk.LEFT, padx=2)
    
    def setup_subscriptions(self):
        pass
    
    def refresh_from_state(self):
        pass
    
    def show_counter(self):
        self.pub_switch_slot("main", CounterContainer)
    
    def show_settings(self):
        self.pub_switch_slot("main", SettingsContainer)

class SettingsContainer(ContainerComponentTk[CounterState]):
    def setup_ui(self):
        tk.Label(self, text="設定画面", font=("Arial", 24)).pack(pady=50)
        tk.Button(self, text="カウンターに戻る", 
                 command=self.back_to_counter).pack()
    
    def setup_subscriptions(self):
        pass
    
    def refresh_from_state(self):
        pass
    
    def back_to_counter(self):
        self.pub_switch_slot("main", CounterContainer)

# テンプレートを使用したアプリケーション
if __name__ == "__main__":
    app = TkApplication(CounterState, title="Multi-Screen Counter App")
    app.pub_register_processor(CounterProcessor)
    
    # テンプレート設定
    app.set_template(AppTemplate)
    app.pub_switch_slot("header", HeaderContainer)
    app.pub_switch_slot("main", CounterContainer)
    
    app.run()
```

## 🎨 スタイリング

### テーマ対応アプリケーション

```python
from pubsubtk import ThemedApplication

# テーマ付きアプリケーション
app = ThemedApplication(
    CounterState, 
    theme="arc",  # arc, equilux, adapta など
    title="Themed Counter App"
)
```

### カスタムスタイル

```python
from tkinter import ttk

class StyledCounterContainer(ContainerComponentTtk[CounterState]):
    def setup_ui(self):
        # ttk.Styleを使用
        style = ttk.Style()
        style.configure("Big.TLabel", font=("Arial", 32))
        
        self.count_label = ttk.Label(self, text="0", style="Big.TLabel")
        self.count_label.pack(pady=20)
        
        # テーマ対応ボタン
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="-", command=self.decrement).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="+", command=self.increment).pack(side=tk.LEFT, padx=5)
```

## 🔧 デバッグ・開発支援

### PubSubデバッグログ

```python
from pubsubtk import enable_pubsub_debug_logging

# 開発時にPubSubの動作を確認
enable_pubsub_debug_logging()

app = TkApplication(CounterState)
# ... アプリケーション設定 ...
app.run()
```

### 非同期処理

```python
from pubsubtk import make_async_task
import asyncio

class AsyncCounterContainer(ContainerComponentTk[CounterState]):
    @make_async_task
    async def slow_increment(self):
        """重い処理をシミュレート"""
        await asyncio.sleep(1)  # 1秒待機
        state = self.store.get_current_state()  
        self.pub_update_state(self.store.state.count, state.count + 1)

# 非同期対応で起動
if __name__ == "__main__":
    app = TkApplication(CounterState)
    app.switch_container(AsyncCounterContainer)
    app.run(use_async=True)  # 非同期モードで起動
```

## 📚 次のステップ

基本的な使い方を理解したら、以下を参照してさらに深く学習しましょう：

- **[Examples](examples.md)** - より実践的なサンプルコード
- **[API Reference](api/)** - 全メソッドの詳細仕様
- **GitHub Repository** - サンプルアプリケーション

## 💡 ベストプラクティス

### 1. 状態設計

```python
# ✅ Good: 正規化された状態
class AppState(BaseModel):
    todos: List[TodoItem] = []
    ui_state: UIState = UIState()
    user_settings: UserSettings = UserSettings()

# ❌ Bad: フラットすぎる状態
class AppState(BaseModel):
    todo_text_1: str = ""
    todo_completed_1: bool = False
    todo_text_2: str = ""
    todo_completed_2: bool = False
    # ...
```

### 2. コンポーネント分離

```python
# ✅ Good: 責任の分離
class TodoListContainer(ContainerComponentTk):
    """状態管理とイベント処理"""
    pass

class TodoItemView(PresentationalComponentTk):
    """純粋な表示"""
    pass

class TodoProcessor(ProcessorBase):
    """ビジネスロジック"""
    pass
```

### 3. StateProxyの活用

```python
# ✅ Good: IDEサポートを活用
self.pub_update_state(self.store.state.todos, updated_todos)
self.sub_state_changed(self.store.state.filter_mode, self.on_filter_changed)

# ❌ Bad: 文字列ハードコード
self.pub_update_state("todos", updated_todos)
self.sub_state_changed("filter_mode", self.on_filter_changed)
```

---

準備完了です！本格的なGUIアプリケーション開発を始めましょう 🚀
