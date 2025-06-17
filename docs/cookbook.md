# 実装レシピ集（Cookbook）

PubSubTkでよく使う「ちょいネタ」や実践Tipsをまとめています。

---

## サブウィンドウへデータを渡す

```python
# サブウィンドウの表示
app.pub_open_subwindow(DialogContainer, kwargs={"item_id": 123})

# DialogContainer側
class DialogContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        item_id = self.kwargs.get("item_id")
        ...
```

---

## Undo/Redoの実装パターン

### パターン1: 組み込みUndo/Redo機能（推奨）

**ポイント:**
特定のフィールドに対して細かくUndo/Redo履歴を管理する最新の方式です。メモリ効率が良く、複数フィールドの独立した履歴管理が可能です。

```python
from pydantic import BaseModel
from pubsubtk import TkApplication, ContainerComponentTk

class AppState(BaseModel):
    counter: int = 0
    text: str = ""

class MainContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        import tkinter as tk
        
        # カウンターエリア
        counter_frame = tk.Frame(self)
        counter_frame.pack(pady=10)
        
        self.counter_label = tk.Label(counter_frame, text="0")
        self.counter_label.pack(side=tk.LEFT)
        
        tk.Button(counter_frame, text="+", command=self.increment).pack(side=tk.LEFT)
        
        # Undo/Redoボタン
        undo_frame = tk.Frame(self)
        undo_frame.pack(pady=5)
        
        self.undo_btn = tk.Button(undo_frame, text="Undo", command=self.undo_counter)
        self.undo_btn.pack(side=tk.LEFT)
        
        self.redo_btn = tk.Button(undo_frame, text="Redo", command=self.redo_counter)
        self.redo_btn.pack(side=tk.LEFT)
    
    def setup_subscriptions(self):
        # カウンターのUndo/Redo機能を有効化（履歴50件まで保持）
        self.pub_enable_undo_redo(self.store.state.counter, max_history=50)
        
        # 状態変更とUndo/Redo可否状態を監視
        self.sub_state_changed(self.store.state.counter, self.on_counter_changed)
        self.sub_undo_status(self.store.state.counter, self.on_undo_status_changed)
    
    def refresh_from_state(self):
        state = self.store.get_current_state()
        self.counter_label.config(text=str(state.counter))
    
    def on_counter_changed(self, old_value, new_value):
        self.counter_label.config(text=str(new_value))
    
    def on_undo_status_changed(self, can_undo, can_redo, undo_count, redo_count):
        # ボタンの有効/無効を切り替え
        self.undo_btn.config(state="normal" if can_undo else "disabled")
        self.redo_btn.config(state="normal" if can_redo else "disabled")
        
        # ツールチップ更新（optional）
        self.undo_btn.config(text=f"Undo ({undo_count})")
        self.redo_btn.config(text=f"Redo ({redo_count})")
    
    def increment(self):
        state = self.store.get_current_state()
        self.pub_update_state(self.store.state.counter, state.counter + 1)
    
    def undo_counter(self):
        self.pub_undo(self.store.state.counter)
    
    def redo_counter(self):
        self.pub_redo(self.store.state.counter)

if __name__ == "__main__":
    app = TkApplication(AppState, title="Undo/Redo Demo")
    app.switch_container(MainContainer)
    app.run()
```

### パターン2: 状態全体のスナップショット方式（レガシー）

**ポイント:**
アプリの状態全体を`model_dump()`で履歴として保持し、`pub_replace_state()`で復元します。シンプルですがメモリ使用量が多くなることがあります。

```python
from pydantic import BaseModel, Field
from typing import Any, List

class AppState(BaseModel):
    value: int = 0
    past: List[Any] = Field(default_factory=list)
    future: List[Any] = Field(default_factory=list)

# 状態を変更する前に「現状態」をpastに追加する
def set_value(self, new_value):
    state = self.store.get_current_state()
    # 現在のスナップショットを履歴に積む
    past = state.past + [state.model_dump()]
    self.pub_update_state(self.store.state.past, past)
    self.pub_update_state(self.store.state.future, [])
    self.pub_update_state(self.store.state.value, new_value)

def undo(self):
    state = self.store.get_current_state()
    if state.past:
        prev = state.past[-1]
        self.pub_update_state(self.store.state.future, [state.model_dump()] + state.future)
        self.pub_replace_state(AppState(**prev))
        self.pub_update_state(self.store.state.past, state.past[:-1])

def redo(self):
    state = self.store.get_current_state()
    if state.future:
        next_state = state.future[0]
        self.pub_update_state(self.store.state.past, state.past + [state.model_dump()])
        self.pub_replace_state(AppState(**next_state))
        self.pub_update_state(self.store.state.future, state.future[1:])
```

---

## 複数フィールドでのUndo/Redo使い分け

```python
class AppState(BaseModel):
    text_content: str = ""
    font_size: int = 12
    color: str = "black"

class EditorContainer(ContainerComponentTk[AppState]):
    def setup_subscriptions(self):
        # テキスト内容は大量履歴で管理
        self.pub_enable_undo_redo(self.store.state.text_content, max_history=100)
        
        # フォントサイズは少ない履歴で十分
        self.pub_enable_undo_redo(self.store.state.font_size, max_history=20)
        
        # 色変更も履歴管理
        self.pub_enable_undo_redo(self.store.state.color, max_history=10)
        
        # それぞれ独立してUndo/Redo状態を監視
        self.sub_undo_status(self.store.state.text_content, self.on_text_undo_status)
        self.sub_undo_status(self.store.state.font_size, self.on_font_undo_status)
    
    def undo_text(self):
        self.pub_undo(self.store.state.text_content)
    
    def undo_font_size(self):
        self.pub_undo(self.store.state.font_size)
```

---

## グローバルショートカット

```python
# tkinterのbindで対応可能
root.bind('<Control-s>', lambda e: app.publish(SaveEvents.SAVE))
root.bind('<Control-z>', lambda e: self.pub_undo(self.store.state.main_content))
root.bind('<Control-y>', lambda e: self.pub_redo(self.store.state.main_content))
```

---

## JSONファイル保存/読込

```python
import json
from tkinter import filedialog

def save_to_json(state):
    path = filedialog.asksaveasfilename(defaultextension=".json")
    if path:
        with open(path, "w") as f:
            json.dump(state.model_dump(), f, indent=2)

def load_from_json():
    path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if path:
        with open(path, "r") as f:
            data = json.load(f)
        # Pydanticモデルで検証
        return AppState.model_validate(data)
```

---

## 任意PubSubイベントの発行

```python
from pubsubtk import AutoNamedTopic
from enum import auto

class MyEvents(AutoNamedTopic):
    EXPORT = auto()

# 発行
self.publish(MyEvents.EXPORT, filepath="output.csv")

# 購読
self.subscribe(MyEvents.EXPORT, self.on_export)
```

---

## カスタムコンポーネントの作り方

```python
from pubsubtk import PresentationalComponentTk

class MyButton(PresentationalComponentTk):
    def setup_ui(self):
        import tkinter as tk
        self.button = tk.Button(self, text="押して！", command=self.on_click)
        self.button.pack()
    def on_click(self):
        self.trigger_event("clicked")
```

---

他にも「Tips追加」歓迎！コントリビュートやIssueで提案してください。
