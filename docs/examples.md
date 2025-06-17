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

## 2. テキストエディタ（Undo/Redo機能付き）

組み込みUndo/Redo機能を活用したテキストエディタのサンプルです。

```python
from pydantic import BaseModel
from pubsubtk import TkApplication, ContainerComponentTk
import tkinter as tk
from tkinter import scrolledtext

class EditorState(BaseModel):
    content: str = ""
    font_size: int = 12

class TextEditorContainer(ContainerComponentTk[EditorState]):
    def setup_ui(self):
        # メニューバー風のツールバー
        toolbar = tk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Undo/Redoボタン
        self.undo_btn = tk.Button(toolbar, text="Undo", command=self.undo_text)
        self.undo_btn.pack(side=tk.LEFT, padx=2)
        
        self.redo_btn = tk.Button(toolbar, text="Redo", command=self.redo_text)
        self.redo_btn.pack(side=tk.LEFT, padx=2)
        
        tk.Frame(toolbar, width=20).pack(side=tk.LEFT)  # スペーサー
        
        # フォントサイズ調整
        tk.Label(toolbar, text="Size:").pack(side=tk.LEFT)
        tk.Button(toolbar, text="-", command=self.decrease_font).pack(side=tk.LEFT)
        self.font_label = tk.Label(toolbar, text="12", width=3)
        self.font_label.pack(side=tk.LEFT)
        tk.Button(toolbar, text="+", command=self.increase_font).pack(side=tk.LEFT)
        
        self.font_undo_btn = tk.Button(toolbar, text="Undo Size", command=self.undo_font)
        self.font_undo_btn.pack(side=tk.LEFT, padx=(10, 2))
        
        # テキストエリア
        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # テキスト変更の遅延処理用
        self._text_change_timer = None
        self.text_area.bind("<KeyRelease>", self.on_text_modified)
        self.text_area.bind("<ButtonRelease>", self.on_text_modified)
    
    def setup_subscriptions(self):
        # テキスト内容のUndo/Redo（大量履歴）
        self.pub_enable_undo_redo(self.store.state.content, max_history=100)
        
        # フォントサイズのUndo/Redo（少ない履歴）
        self.pub_enable_undo_redo(self.store.state.font_size, max_history=20)
        
        # 状態変更の監視
        self.sub_state_changed(self.store.state.content, self.on_content_changed)
        self.sub_state_changed(self.store.state.font_size, self.on_font_size_changed)
        
        # Undo/Redo状態の監視
        self.sub_undo_status(self.store.state.content, self.on_text_undo_status)
        self.sub_undo_status(self.store.state.font_size, self.on_font_undo_status)
    
    def refresh_from_state(self):
        state = self.store.get_current_state()
        # テキスト内容を同期
        if self.text_area.get("1.0", tk.END).rstrip("\n") != state.content:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", state.content)
        # フォントサイズを同期
        self.update_font_size(state.font_size)
    
    def on_text_modified(self, event=None):
        # 入力中の頻繁な更新を避けるため、遅延処理
        if self._text_change_timer:
            self.after_cancel(self._text_change_timer)
        self._text_change_timer = self.after(1000, self.save_text_content)
    
    def save_text_content(self):
        content = self.text_area.get("1.0", tk.END).rstrip("\n")
        self.pub_update_state(self.store.state.content, content)
        self._text_change_timer = None
    
    def on_content_changed(self, old_value, new_value):
        # 外部からの変更時のみ更新（自分の変更は無視）
        current = self.text_area.get("1.0", tk.END).rstrip("\n")
        if current != new_value:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", new_value)
    
    def on_font_size_changed(self, old_value, new_value):
        self.update_font_size(new_value)
    
    def update_font_size(self, size):
        self.text_area.config(font=("TkDefaultFont", size))
        self.font_label.config(text=str(size))
    
    def on_text_undo_status(self, can_undo, can_redo, undo_count, redo_count):
        self.undo_btn.config(state="normal" if can_undo else "disabled")
        self.redo_btn.config(state="normal" if can_redo else "disabled")
        self.undo_btn.config(text=f"Undo ({undo_count})" if undo_count > 0 else "Undo")
        self.redo_btn.config(text=f"Redo ({redo_count})" if redo_count > 0 else "Redo")
    
    def on_font_undo_status(self, can_undo, can_redo, undo_count, redo_count):
        self.font_undo_btn.config(state="normal" if can_undo else "disabled")
    
    def undo_text(self):
        self.save_text_content()  # 現在の内容を保存してからUndo
        self.pub_undo(self.store.state.content)
    
    def redo_text(self):
        self.pub_redo(self.store.state.content)
    
    def increase_font(self):
        state = self.store.get_current_state()
        if state.font_size < 72:
            self.pub_update_state(self.store.state.font_size, state.font_size + 2)
    
    def decrease_font(self):
        state = self.store.get_current_state()
        if state.font_size > 8:
            self.pub_update_state(self.store.state.font_size, state.font_size - 2)
    
    def undo_font(self):
        self.pub_undo(self.store.state.font_size)

if __name__ == "__main__":
    app = TkApplication(EditorState, title="Text Editor with Undo/Redo")
    app.switch_container(TextEditorContainer)
    app.run()
```

---

## 3. データビューア（CSV/JSON表示）

CSVやJSONを読み込んでテーブル表示・編集するアプリ例（詳細はCookbookやGitHub参照）。

---

## 4. PubSubDefaultTopicBaseの全メソッドデモ

**PubSubDefaultTopicBaseの全メソッドを使ったコンパクトなデモアプリケーション**
各種画面遷移・状態変更・サブウィンドウ・Processor動的登録など、フレームワークの使い方を総合的に確認したい方は[こちらのデモコード](ai-reference/REFERENCE_FULL.md/#実践例)も参照してください。

---

## 5. 他にも…

* 設定ダイアログ付きツール
* マルチ画面ウィザード
* ダッシュボード系アプリ

詳細や小技は [レシピ集](cookbook.md) もご参照ください。
