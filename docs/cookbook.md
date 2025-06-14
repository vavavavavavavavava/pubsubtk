
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

## Undo/Redoの基本実装（状態全体のスナップショット方式）

**ポイント:**
アプリの状態全体を`model_dump()`で履歴として保持し、`pub_replace_state()`で復元します。

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

* 状態変更前に`past`に現在のスナップショットを`model_dump()`で追加
* `undo`は`past`から復元、`redo`は`future`から復元

---

## グローバルショートカット

```python
# tkinterのbindで対応可能
root.bind('<Control-s>', lambda e: app.publish(SaveEvents.SAVE))
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
