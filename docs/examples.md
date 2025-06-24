# サンプル集

PubSubTkを使った現実的なGUIアプリケーション例を紹介します。

---

## 1. Todoアプリ（状態管理・リスト操作・画面遷移）

状態定義・ビジネスロジック・UIコンポーネントの3層分離を活用した典型的な例です。

```python
from pydantic import BaseModel
from typing import List
from pubsubtk import TkApplication, ContainerComponentTk, ProcessorBase, AutoNamedTopic
from enum import auto

class TodoItem(BaseModel):
    id: int
    text: str
    done: bool = False

class AppState(BaseModel):
    todos: List[TodoItem] = []
    next_id: int = 1

class Events(AutoNamedTopic):
    ADD = auto()
    TOGGLE = auto()
    DELETE = auto()

class MainProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe(Events.ADD, self.add)
        self.subscribe(Events.TOGGLE, self.toggle)
        self.subscribe(Events.DELETE, self.delete)
    def add(self, text: str):
        state = self.store.get_current_state()
        todo = TodoItem(id=state.next_id, text=text)
        self.pub_add_to_list(self.store.state.todos, todo)
        self.pub_update_state(self.store.state.next_id, state.next_id + 1)
    def toggle(self, todo_id: int):
        state = self.store.get_current_state()
        new_todos = [
            TodoItem(**dict(t), done=not t.done) if t.id == todo_id else t
            for t in state.todos
        ]
        self.pub_update_state(self.store.state.todos, new_todos)
    def delete(self, todo_id: int):
        state = self.store.get_current_state()
        new_todos = [t for t in state.todos if t.id != todo_id]
        self.pub_update_state(self.store.state.todos, new_todos)

class TodoContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        import tkinter as tk
        self.entry = tk.Entry(self)
        self.entry.pack(fill=tk.X, padx=5, pady=5)
        self.entry.bind("<Return>", lambda e: self.on_add())
        tk.Button(self, text="追加", command=self.on_add).pack()
        self.list_frame = tk.Frame(self)
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        self.todo_widgets = {}
    def setup_subscriptions(self):
        self.sub_for_refresh(self.store.state.todos, self.refresh_list)
    def refresh_from_state(self):
        self.refresh_list()
    def refresh_list(self):
        for w in self.todo_widgets.values():
            w.destroy()
        self.todo_widgets.clear()
        state = self.store.get_current_state()
        for todo in state.todos:
            self.add_todo_widget(todo)
    def add_todo_widget(self, todo):
        import tkinter as tk
        f = tk.Frame(self.list_frame)
        f.pack(fill=tk.X, pady=2)
        var = tk.BooleanVar(value=todo.done)
        chk = tk.Checkbutton(f, variable=var, command=lambda: self.on_toggle(todo.id))
        chk.pack(side=tk.LEFT)
        lbl = tk.Label(f, text=todo.text)
        lbl.pack(side=tk.LEFT, padx=5)
        btn = tk.Button(f, text="削除", command=lambda: self.on_delete(todo.id))
        btn.pack(side=tk.RIGHT)
        self.todo_widgets[todo.id] = f
    def on_add(self):
        text = self.entry.get().strip()
        if text:
            self.publish(Events.ADD, text=text)
            self.entry.delete(0, 'end')
    def on_toggle(self, todo_id: int):
        self.publish(Events.TOGGLE, todo_id=todo_id)
    def on_delete(self, todo_id: int):
        self.publish(Events.DELETE, todo_id=todo_id)

if __name__ == "__main__":
    app = TkApplication(AppState, title="Todo App")
    app.pub_register_processor(MainProcessor)
    app.switch_container(TodoContainer)
    app.run()
```

---

## 2. データビューア（CSV/JSON表示）

CSVやJSONを読み込んでテーブル表示・編集するアプリ例（詳細はCookbookやGitHub参照）。

---

## 3. PubSubDefaultTopicBaseの全メソッドデモ

**PubSubDefaultTopicBaseの全メソッドを使ったコンパクトなデモアプリケーション**
各種画面遷移・状態変更・サブウィンドウ・Processor動的登録など、フレームワークの使い方を総合的に確認したい方は[こちらのデモコード](ai-reference/REFERENCE_FULL.md/#実践例)も参照してください。

---

## 4. Storybookを使ったコンポーネントカタログ

UIコンポーネントライブラリをStorybookで開発・確認する完全な例です。

```python
# components/buttons.py
from pubsubtk import PresentationalComponentTk
from pubsubtk.storybook import story
import tkinter as tk

class PrimaryButton(PresentationalComponentTk):
    def setup_ui(self):
        self.button = tk.Button(
            self,
            bg="#007bff",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.button.pack()
        
    def set_text(self, text: str):
        self.button.config(text=text)
        
    def set_command(self, command):
        self.button.config(command=command)

@story("Buttons.Primary")
def primary_button_story(ctx):
    text = ctx.knob("text", str, "Primary Button")
    enabled = ctx.knob("enabled", bool, True)
    
    btn = PrimaryButton(ctx.parent)
    btn.set_text(text.value)
    btn.button.config(state="normal" if enabled.value else "disabled")
    
    # Knob変更時の更新
    text.add_change_callback(lambda v: btn.set_text(v))
    enabled.add_change_callback(
        lambda v: btn.button.config(state="normal" if v else "disabled")
    )
    
    btn.pack(padx=20, pady=20)
    return btn

# components/forms.py
from tkinter import ttk

class FormField(PresentationalComponentTk):
    def setup_ui(self):
        self.label = ttk.Label(self)
        self.label.pack(anchor="w")
        
        self.entry = ttk.Entry(self, width=40)
        self.entry.pack(fill="x", pady=(5, 0))
        
        self.error_label = ttk.Label(self, foreground="red", font=("Arial", 8))
        self.error_label.pack(anchor="w")
        
    def set_label(self, text: str):
        self.label.config(text=text)
        
    def set_error(self, error: str):
        self.error_label.config(text=error)
        
    def get_value(self):
        return self.entry.get()

@story("Forms.TextField")
def text_field_story(ctx):
    label = ctx.knob("label", str, "Email Address")
    placeholder = ctx.knob("placeholder", str, "user@example.com")
    required = ctx.knob("required", bool, True)
    error = ctx.knob("error", str, "", desc="Error message to display")
    
    field = FormField(ctx.parent)
    field.set_label(label.value + (" *" if required.value else ""))
    field.entry.insert(0, placeholder.value)
    field.set_error(error.value)
    
    # 動的更新
    label.add_change_callback(
        lambda v: field.set_label(v + (" *" if required.value else ""))
    )
    error.add_change_callback(lambda v: field.set_error(v))
    
    field.pack(padx=20, pady=20, fill="x")
    return field

# run_storybook.py
from pubsubtk.storybook import StorybookApplication
from pubsubtk.storybook.core.auto_discover import discover_stories

if __name__ == "__main__":
    # components/以下の全ストーリーを自動検出
    discover_stories("components")
    
    app = StorybookApplication(
        theme="arc",
        title="My Component Library",
        geometry="1400x900"
    )
    app.run()
```

---

## 5. 複合的なStorybookサンプル（状態付きコンポーネント）

```python
# components/counter_widget.py
from pubsubtk import ContainerComponentTk
from pubsubtk.storybook import story, StoryContext
from pydantic import BaseModel
import tkinter as tk

class CounterState(BaseModel):
    count: int = 0

class CounterWidget(ContainerComponentTk[CounterState]):
    def setup_ui(self):
        self.label = tk.Label(self, font=("Arial", 24))
        self.label.pack(pady=10)
        
        button_frame = tk.Frame(self)
        button_frame.pack()
        
        tk.Button(button_frame, text="-", command=self.decrement).pack(side="left", padx=5)
        tk.Button(button_frame, text="+", command=self.increment).pack(side="left", padx=5)
        tk.Button(button_frame, text="Reset", command=self.reset).pack(side="left", padx=5)
        
    def setup_subscriptions(self):
        self.sub_for_refresh(self.store.state.count, self.update_display)
        
    def refresh_from_state(self):
        self.update_display()
        
    def update_display(self):
        count = self.store.get_current_state().count
        self.label.config(text=str(count))
        
    def increment(self):
        state = self.store.get_current_state()
        self.pub_update_state(self.store.state.count, state.count + 1)
        
    def decrement(self):
        state = self.store.get_current_state()
        self.pub_update_state(self.store.state.count, state.count - 1)
        
    def reset(self):
        self.pub_update_state(self.store.state.count, 0)

@story("Widgets.Counter")
def counter_story(ctx: StoryContext):
    # Knobでカスタマイズ
    initial_value = ctx.knob("initialValue", int, 0, range_=(-100, 100))
    step = ctx.knob("step", int, 1, range_=(1, 10))
    
    # ローカルストアを作成
    from pubsubtk import get_store
    store = get_store(CounterState)
    
    # 初期値を設定
    store.update_state("count", initial_value.value)
    
    # ウィジェットを作成
    counter = CounterWidget(ctx.parent, store=store)
    
    # stepに応じてincrement/decrementを調整
    original_increment = counter.increment
    original_decrement = counter.decrement
    
    def custom_increment():
        state = store.get_current_state()
        store.update_state("count", state.count + step.value)
        
    def custom_decrement():
        state = store.get_current_state()
        store.update_state("count", state.count - step.value)
        
    counter.increment = custom_increment
    counter.decrement = custom_decrement
    
    counter.pack(padx=40, pady=40)
    return counter
```

---

## 6. 他にも…

* 設定ダイアログ付きツール
* マルチ画面ウィザード
* ダッシュボード系アプリ

詳細や小技は [レシピ集](cookbook.md) もご参照ください。
