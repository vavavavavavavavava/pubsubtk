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

## 4. 他にも…

* 設定ダイアログ付きツール
* マルチ画面ウィザード
* ダッシュボード系アプリ

詳細や小技は [レシピ集](cookbook.md) もご参照ください。
