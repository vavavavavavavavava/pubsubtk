# はじめに

PubSubTkで、型安全かつ疎結合なGUIアプリケーションを素早く開発しましょう。

## 1. インストール

```bash
pip install git+https://github.com/vavavavavavavavava/pubsubtk
```

## 2. 基本設計と主要パーツ

### Store（状態管理）

Pydanticモデルでアプリケーションの状態を型安全に管理します。

```python
from pydantic import BaseModel

class AppState(BaseModel):
    counter: int = 0
```

### Container（状態連携UI）

状態を購読しUIを自動更新するスマート部品です。

```python
from pubsubtk import ContainerComponentTk

class Main(ContainerComponentTk[AppState]):
    def setup_ui(self):
        ...
    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.counter, self.on_counter_changed)
    def on_counter_changed(self, _, new):
        ...
```

### Presentational（純粋表示部品）

データを受け取って表示するだけのダム部品です。

```python
from pubsubtk import PresentationalComponentTk

class CounterView(PresentationalComponentTk):
    def setup_ui(self):
        ...
    def update_data(self, value: int):
        ...
```

### Processor（ロジック分離・状態操作）

ビジネスロジックや複雑な状態変化はProcessorに集約できます。

```python
from pubsubtk import ProcessorBase, AutoNamedTopic
from enum import auto

class Events(AutoNamedTopic):
    INCREMENT = auto()

class MainProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe(Events.INCREMENT, self.inc)
    def inc(self):
        ...
```

## 3. 最小アプリを作ってみる

```python
from pubsubtk import TkApplication, ContainerComponentTk
from pydantic import BaseModel

class AppState(BaseModel):
    count: int = 0

class Main(ContainerComponentTk[AppState]):
    def setup_ui(self):
        import tkinter as tk
        self.label = tk.Label(self, text="0")
        self.label.pack()
        tk.Button(self, text="増やす", command=self.inc).pack()
    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.count, self.on_count)
    def on_count(self, _, new): self.label.config(text=str(new))
    def inc(self):
        state = self.store.get_current_state()
        self.pub_update_state(self.store.state.count, state.count + 1)

if __name__ == "__main__":
    app = TkApplication(AppState, title="Demo")
    app.switch_container(Main)
    app.run()
```

## 4. Undo/Redo機能を追加してみる

PubSubTkでは組み込みのUndo/Redo機能を簡単に追加できます：

```python
class Main(ContainerComponentTk[AppState]):
    def setup_ui(self):
        import tkinter as tk
        
        # カウンター表示
        self.label = tk.Label(self, text="0")
        self.label.pack()
        
        # 操作ボタン
        button_frame = tk.Frame(self)
        button_frame.pack()
        tk.Button(button_frame, text="増やす", command=self.inc).pack(side=tk.LEFT)
        
        # Undo/Redoボタン
        self.undo_btn = tk.Button(button_frame, text="Undo", command=self.undo)
        self.undo_btn.pack(side=tk.LEFT)
        self.redo_btn = tk.Button(button_frame, text="Redo", command=self.redo)
        self.redo_btn.pack(side=tk.LEFT)
    
    def setup_subscriptions(self):
        # Undo/Redo機能を有効化（履歴20件まで保持）
        self.pub_enable_undo_redo(self.store.state.count, max_history=20)
        
        # 状態変更とUndo/Redo可否を監視
        self.sub_state_chang
