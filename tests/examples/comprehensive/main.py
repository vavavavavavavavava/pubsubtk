"""
PubSubTk 全機能コンパクトデモ

PubSubDefaultTopicBaseの全メソッドを使用した小規模なデモアプリケーション
"""

import asyncio
import json
import tkinter as tk
from enum import auto
from tkinter import filedialog, messagebox, simpledialog
from typing import List

from pydantic import BaseModel

from pubsubtk import (
    AutoNamedTopic,
    ContainerComponentTk,
    PresentationalComponentTk,
    ProcessorBase,
    TemplateComponentTk,
    TkApplication,
    make_async_task,
)


# カスタムトピック
class AppTopic(AutoNamedTopic):
    INCREMENT = auto()
    RESET = auto()
    MILESTONE = auto()


# データモデル
class TodoItem(BaseModel):
    id: int
    text: str
    completed: bool = False


class AppState(BaseModel):
    counter: int = 0
    total_clicks: int = 0
    todos: List[TodoItem] = []
    next_todo_id: int = 1
    settings: dict = {"theme": "default", "auto_save": "true"}
    current_view: str = "main"


# =============================================================================
# テンプレート（3スロット構成）
# =============================================================================


class AppTemplate(TemplateComponentTk[AppState]):
    def define_slots(self):
        # ナビゲーション
        self.navbar = tk.Frame(self, height=40, bg="navy")
        self.navbar.pack(fill=tk.X)
        self.navbar.pack_propagate(False)

        # メインコンテンツ
        self.main_area = tk.Frame(self)
        self.main_area.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # サイドバー
        self.sidebar = tk.Frame(self, width=200, bg="lightgray")
        self.sidebar.pack(fill=tk.Y, side=tk.RIGHT)
        self.sidebar.pack_propagate(False)

        return {
            "navbar": self.navbar,
            "main": self.main_area,
            "sidebar": self.sidebar,
        }


# =============================================================================
# Presentationalコンポーネント（純粋表示）
# =============================================================================


class UndoRedoControlView(PresentationalComponentTk):
    """Undo/Redo操作用のPresentationalコンポーネント"""

    def setup_ui(self):
        self.configure(relief=tk.RIDGE, borderwidth=1, bg="lightyellow")

        # タイトル
        title_label = tk.Label(
            self, text="🔄 履歴操作", font=("Arial", 10, "bold"), bg="lightyellow"
        )
        title_label.pack(pady=2)

        # ボタンフレーム
        btn_frame = tk.Frame(self, bg="lightyellow")
        btn_frame.pack(pady=2)

        self.undo_btn = tk.Button(btn_frame, text="← Undo", state="disabled", width=8)
        self.undo_btn.pack(side=tk.LEFT, padx=2)

        self.redo_btn = tk.Button(btn_frame, text="Redo →", state="disabled", width=8)
        self.redo_btn.pack(side=tk.LEFT, padx=2)

        # ステータス表示
        self.status_label = tk.Label(
            self, text="無効", font=("Arial", 8), bg="lightyellow", fg="gray"
        )
        self.status_label.pack(pady=1)

    def setup_handlers(self, undo_handler, redo_handler):
        """Undo/Redoハンドラーを設定"""
        self.undo_btn.config(command=undo_handler)
        self.redo_btn.config(command=redo_handler)

    def update_status(
        self, can_undo: bool, can_redo: bool, undo_count: int, redo_count: int
    ):
        """Undo/Redoステータスを更新"""
        # ボタンの有効/無効状態
        self.undo_btn.config(
            state="normal" if can_undo else "disabled",
            text=f"← Undo ({undo_count})" if undo_count > 0 else "← Undo",
        )
        self.redo_btn.config(
            state="normal" if can_redo else "disabled",
            text=f"Redo ({redo_count}) →" if redo_count > 0 else "Redo →",
        )

        # ステータステキスト
        if can_undo or can_redo:
            status = f"Undo:{undo_count} Redo:{redo_count}"
            self.status_label.config(text=status, fg="black")
        else:
            self.status_label.config(text="履歴なし", fg="gray")


class TodoItemView(PresentationalComponentTk):
    def setup_ui(self):
        self.configure(relief=tk.RAISED, borderwidth=1, padx=5, pady=3)

        self.var = tk.BooleanVar()
        self.checkbox = tk.Checkbutton(self, variable=self.var, command=self.on_toggle)
        self.checkbox.pack(side=tk.LEFT)

        self.label = tk.Label(self, text="", anchor="w")
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.delete_btn = tk.Button(self, text="×", width=3, command=self.on_delete)
        self.delete_btn.pack(side=tk.RIGHT)

    def update_data(self, todo: TodoItem):
        self.todo = todo
        self.var.set(todo.completed)
        text = f"✓ {todo.text}" if todo.completed else todo.text
        self.label.config(text=text, fg="gray" if todo.completed else "black")

    def on_toggle(self):
        self.trigger_event("toggle", todo_id=self.todo.id)

    def on_delete(self):
        self.trigger_event("delete", todo_id=self.todo.id)


class StatsView(PresentationalComponentTk):
    def setup_ui(self):
        self.configure(bg="lightblue", relief=tk.SUNKEN, borderwidth=2)

        tk.Label(self, text="📊 統計", font=("Arial", 12, "bold"), bg="lightblue").pack(
            pady=5
        )

        self.stats_label = tk.Label(self, text="", bg="lightblue", justify=tk.LEFT)
        self.stats_label.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    def update_stats(
        self,
        counter: int,
        total_clicks: int,
        total_todos: int,
        completed_todos: int,
        settings_count: int,
        current_view: str,
        counter_undo_status: dict = None,
        todos_undo_status: dict = None,
    ):
        """純粋な表示コンポーネント - 必要なデータのみを個別に受け取る"""
        uncompleted = total_todos - completed_todos

        # デフォルト値設定
        counter_undo_status = counter_undo_status or {
            "can_undo": False,
            "can_redo": False,
            "undo_count": 0,
            "redo_count": 0,
        }
        todos_undo_status = todos_undo_status or {
            "can_undo": False,
            "can_redo": False,
            "undo_count": 0,
            "redo_count": 0,
        }

        stats = f"""カウンター: {counter}
総クリック: {total_clicks}

Todo統計:
・総数: {total_todos}
・完了: {completed_todos}
・未完了: {uncompleted}

設定数: {settings_count}
現在画面: {current_view}

🔄 履歴状況:
カウンター履歴:
・Undo: {counter_undo_status["undo_count"]}回
・Redo: {counter_undo_status["redo_count"]}回

Todo履歴:
・Undo: {todos_undo_status["undo_count"]}回
・Redo: {todos_undo_status["redo_count"]}回"""

        self.stats_label.config(text=stats)


# =============================================================================
# Containerコンポーネント（状態連携）
# =============================================================================


class NavbarContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        self.configure(bg="navy")

        tk.Label(
            self,
            text="🎯 PubSubTk Demo (w/ Undo/Redo)",
            fg="white",
            bg="navy",
            font=("Arial", 14, "bold"),
        ).pack(side=tk.LEFT, padx=10, pady=5)

        nav_frame = tk.Frame(self, bg="navy")
        nav_frame.pack(side=tk.RIGHT, padx=10)

        self.main_btn = tk.Button(nav_frame, text="メイン", command=self.switch_to_main)
        self.main_btn.pack(side=tk.LEFT, padx=2)

        self.todo_btn = tk.Button(nav_frame, text="Todo", command=self.switch_to_todo)
        self.todo_btn.pack(side=tk.LEFT, padx=2)

    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.current_view, self.on_view_changed)

    def refresh_from_state(self):
        state = self.store.get_current_state()
        self.update_buttons(state.current_view)

    def on_view_changed(self, old_value, new_value):
        self.update_buttons(new_value)

    def update_buttons(self, current_view: str):
        self.main_btn.config(
            bg="lightblue" if current_view == "main" else "SystemButtonFace"
        )
        self.todo_btn.config(
            bg="lightblue" if current_view == "todo" else "SystemButtonFace"
        )

    def switch_to_main(self):
        self.pub_update_state(self.store.state.current_view, "main")
        self.pub_switch_slot("main", MainContainer)

    def switch_to_todo(self):
        self.pub_update_state(self.store.state.current_view, "todo")
        self.pub_switch_slot("main", TodoContainer)


class MainContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        tk.Label(self, text="🏠 メインビュー", font=("Arial", 16, "bold")).pack(pady=10)

        # カウンター
        self.counter_label = tk.Label(self, text="0", font=("Arial", 32))
        self.counter_label.pack(pady=20)

        # Undo/Redoコントロール（カウンター用）
        self.counter_undo_control = UndoRedoControlView(self)
        self.counter_undo_control.pack(pady=5)
        self.counter_undo_control.setup_handlers(
            undo_handler=self.undo_counter, redo_handler=self.redo_counter
        )

        # ボタン群
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="カウント", command=self.increment).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btn_frame, text="リセット", command=self.reset).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btn_frame, text="サブウィンドウ", command=self.open_sub).pack(
            side=tk.LEFT, padx=5
        )

        # Undo/Redo制御ボタン
        undo_control_frame = tk.Frame(self)
        undo_control_frame.pack(pady=5)

        self.enable_undo_btn = tk.Button(
            undo_control_frame,
            text="履歴記録ON",
            command=self.enable_counter_undo,
            bg="lightgreen",
        )
        self.enable_undo_btn.pack(side=tk.LEFT, padx=5)

        self.disable_undo_btn = tk.Button(
            undo_control_frame,
            text="履歴記録OFF",
            command=self.disable_counter_undo,
            bg="lightcoral",
            state="disabled",
        )
        self.disable_undo_btn.pack(side=tk.LEFT, padx=5)

        # ファイル操作
        file_frame = tk.Frame(self)
        file_frame.pack(pady=10)

        tk.Button(file_frame, text="保存", command=self.save_data).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(file_frame, text="読込", command=self.load_data).pack(
            side=tk.LEFT, padx=5
        )

        # 設定操作（辞書機能テスト）
        setting_frame = tk.Frame(self)
        setting_frame.pack(pady=10)

        tk.Button(setting_frame, text="設定追加", command=self.add_setting).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(
            setting_frame, text="プロセッサー追加", command=self.add_processor
        ).pack(side=tk.LEFT, padx=5)

        # 危険な操作
        tk.Button(
            self, text="全状態リセット", command=self.reset_all, bg="red", fg="white"
        ).pack(pady=10)

    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.counter, self.on_counter_changed)
        self.subscribe(AppTopic.MILESTONE, self.on_milestone)

        # カウンターのUndo/Redoステータス変化を購読
        self.sub_undo_status(str(self.store.state.counter), self.on_counter_undo_status)

    def refresh_from_state(self):
        state = self.store.get_current_state()
        self.counter_label.config(text=str(state.counter))

    def on_counter_changed(self, old_value, new_value):
        self.counter_label.config(text=str(new_value))

    def on_counter_undo_status(
        self, can_undo: bool, can_redo: bool, undo_count: int, redo_count: int
    ):
        """カウンターのUndo/Redoステータス変化ハンドラー"""
        self.counter_undo_control.update_status(
            can_undo, can_redo, undo_count, redo_count
        )

    def enable_counter_undo(self):
        """カウンターのUndo/Redo機能を有効化"""
        self.pub_enable_undo_redo(str(self.store.state.counter), max_history=20)
        self.enable_undo_btn.config(state="disabled")
        self.disable_undo_btn.config(state="normal")

    def disable_counter_undo(self):
        """カウンターのUndo/Redo機能を無効化"""
        self.pub_disable_undo_redo(str(self.store.state.counter))
        self.enable_undo_btn.config(state="normal")
        self.disable_undo_btn.config(state="disabled")

    def undo_counter(self):
        """カウンターをUndo"""
        self.pub_undo(str(self.store.state.counter))

    def redo_counter(self):
        """カウンターをRedo"""
        self.pub_redo(str(self.store.state.counter))

    def increment(self):
        self.publish(AppTopic.INCREMENT)

    def reset(self):
        self.publish(AppTopic.RESET)

    def open_sub(self):
        self.pub_open_subwindow(SubWindow)

    @make_async_task
    async def save_data(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json")
        if filename:
            await asyncio.sleep(0.3)  # 保存処理シミュレート
            state = self.store.get_current_state()
            with open(filename, "w") as f:
                json.dump(state.model_dump(), f, indent=2)
            messagebox.showinfo("完了", "データを保存しました")

    @make_async_task
    async def load_data(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            await asyncio.sleep(0.3)  # 読込処理シミュレート
            with open(filename, "r") as f:
                data = json.load(f)
            new_state = AppState.model_validate(data)
            self.pub_replace_state(new_state)
            # 状態リセット後は画面も適切に切り替える
            self.pub_switch_slot("main", MainContainer)
            messagebox.showinfo("完了", "データを読み込みました")

    def add_setting(self):
        key = simpledialog.askstring("設定追加", "キーを入力:")
        if key:
            value = simpledialog.askstring("設定追加", "値を入力:")
            if value:
                # pub_add_to_dict使用
                self.pub_add_to_dict(self.store.state.settings, key, value)

    @make_async_task
    async def add_processor(self):
        await asyncio.sleep(0.5)  # プロセッサー初期化シミュレート
        try:
            # pub_register_processor使用
            self.pub_register_processor(DummyProcessor, "dummy")
            messagebox.showinfo("成功", "プロセッサーを追加しました")
        except Exception as e:
            messagebox.showerror("エラー", str(e))

    @make_async_task
    async def reset_all(self):
        if messagebox.askyesno("確認", "全状態をリセットしますか？"):
            await asyncio.sleep(1.0)  # 重い処理シミュレート
            # pub_replace_state使用
            self.pub_replace_state(AppState())
            # リセット後はメイン画面に戻る
            self.pub_switch_slot("main", MainContainer)
            messagebox.showinfo("完了", "状態をリセットしました")

    def on_milestone(self, value: int):
        messagebox.showinfo("マイルストーン!", f"{value}に到達！")


class TodoContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        tk.Label(self, text="📝 Todo管理", font=("Arial", 16, "bold")).pack(pady=10)

        # Todo用Undo/Redoコントロール
        self.todo_undo_control = UndoRedoControlView(self)
        self.todo_undo_control.pack(pady=5)
        self.todo_undo_control.setup_handlers(
            undo_handler=self.undo_todos, redo_handler=self.redo_todos
        )

        # Undo/Redo制御
        undo_control_frame = tk.Frame(self)
        undo_control_frame.pack(pady=5)

        self.enable_todo_undo_btn = tk.Button(
            undo_control_frame,
            text="Todo履歴ON",
            command=self.enable_todo_undo,
            bg="lightgreen",
        )
        self.enable_todo_undo_btn.pack(side=tk.LEFT, padx=5)

        self.disable_todo_undo_btn = tk.Button(
            undo_control_frame,
            text="Todo履歴OFF",
            command=self.disable_todo_undo,
            bg="lightcoral",
            state="disabled",
        )
        self.disable_todo_undo_btn.pack(side=tk.LEFT, padx=5)

        # Todo追加
        add_frame = tk.Frame(self)
        add_frame.pack(fill=tk.X, padx=10, pady=5)

        self.entry = tk.Entry(add_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry.bind("<Return>", lambda e: self.add_todo())

        tk.Button(add_frame, text="追加", command=self.add_todo).pack(side=tk.RIGHT)

        # Todoリスト
        list_frame = tk.Frame(self, relief=tk.SUNKEN, borderwidth=2)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # スクロール可能フレーム
        canvas = tk.Canvas(list_frame)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.todo_widgets = {}

    def setup_subscriptions(self):
        # sub_state_addedとsub_for_refresh使用
        self.sub_state_added(self.store.state.todos, self.on_todo_added)
        self.sub_for_refresh(self.store.state.todos, self.refresh_todo_list)

        # TodoリストのUndo/Redoステータス変化を購読
        self.sub_undo_status(str(self.store.state.todos), self.on_todo_undo_status)

    def refresh_from_state(self):
        self.refresh_todo_list()

    def on_todo_undo_status(
        self, can_undo: bool, can_redo: bool, undo_count: int, redo_count: int
    ):
        """TodoリストのUndo/Redoステータス変化ハンドラー"""
        self.todo_undo_control.update_status(can_undo, can_redo, undo_count, redo_count)

    def enable_todo_undo(self):
        """TodoリストのUndo/Redo機能を有効化"""
        self.pub_enable_undo_redo(str(self.store.state.todos), max_history=15)
        self.enable_todo_undo_btn.config(state="disabled")
        self.disable_todo_undo_btn.config(state="normal")

    def disable_todo_undo(self):
        """TodoリストのUndo/Redo機能を無効化"""
        self.pub_disable_undo_redo(str(self.store.state.todos))
        self.enable_todo_undo_btn.config(state="normal")
        self.disable_todo_undo_btn.config(state="disabled")

    def undo_todos(self):
        """TodoリストをUndo"""
        self.pub_undo(str(self.store.state.todos))

    def redo_todos(self):
        """TodoリストをRedo"""
        self.pub_redo(str(self.store.state.todos))

    def refresh_todo_list(self):
        # 既存ウィジェットクリア
        for widget in self.todo_widgets.values():
            widget.destroy()
        self.todo_widgets.clear()

        # 新しいリストを描画
        state = self.store.get_current_state()
        for todo in state.todos:
            todo_widget = TodoItemView(self.scrollable_frame)
            todo_widget.pack(fill=tk.X, padx=5, pady=2)
            todo_widget.update_data(todo)

            # イベントハンドラ登録
            todo_widget.register_handler("toggle", self.toggle_todo)
            todo_widget.register_handler("delete", self.delete_todo)

            self.todo_widgets[todo.id] = todo_widget

    def on_todo_added(self, item: TodoItem, index: int):
        # 新規追加時は全体再描画
        self.refresh_todo_list()

    def add_todo(self):
        text = self.entry.get().strip()
        if not text:
            return

        state = self.store.get_current_state()
        new_todo = TodoItem(id=state.next_todo_id, text=text)

        # pub_add_to_list使用
        self.pub_add_to_list(self.store.state.todos, new_todo)
        self.pub_update_state(self.store.state.next_todo_id, state.next_todo_id + 1)

        self.entry.delete(0, tk.END)

    def toggle_todo(self, todo_id: int):
        state = self.store.get_current_state()
        updated_todos = []
        for todo in state.todos:
            if todo.id == todo_id:
                updated = todo.model_copy()
                updated.completed = not updated.completed
                updated_todos.append(updated)
            else:
                updated_todos.append(todo)

        self.pub_update_state(self.store.state.todos, updated_todos)

    @make_async_task
    async def delete_todo(self, todo_id: int):
        if messagebox.askyesno("確認", "このTodoを削除しますか？"):
            await asyncio.sleep(0.2)  # 削除処理シミュレート
            state = self.store.get_current_state()
            updated_todos = [t for t in state.todos if t.id != todo_id]
            self.pub_update_state(self.store.state.todos, updated_todos)


class SidebarContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        self.configure(bg="lightgray")

        # 統計表示（Presentationalコンポーネント使用）
        self.stats_view = StatsView(self)
        self.stats_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 操作ボタン
        btn_frame = tk.Frame(self, bg="lightgray")
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="全ウィンドウ閉じる", command=self.close_all).pack(
            fill=tk.X, pady=2
        )
        tk.Button(btn_frame, text="プロセッサー削除", command=self.delete_proc).pack(
            fill=tk.X, pady=2
        )

        # Undo/Redo情報保持用
        self.counter_undo_status = {
            "can_undo": False,
            "can_redo": False,
            "undo_count": 0,
            "redo_count": 0,
        }
        self.todos_undo_status = {
            "can_undo": False,
            "can_redo": False,
            "undo_count": 0,
            "redo_count": 0,
        }

    def setup_subscriptions(self):
        # 複数の状態変更を監視
        self.sub_for_refresh(self.store.state.counter, self.refresh_from_state)
        self.sub_for_refresh(self.store.state.todos, self.refresh_from_state)
        self.sub_for_refresh(self.store.state.settings, self.refresh_from_state)
        self.sub_for_refresh(self.store.state.total_clicks, self.refresh_from_state)
        self.sub_for_refresh(self.store.state.current_view, self.refresh_from_state)

        # sub_dict_item_added使用
        self.sub_dict_item_added(self.store.state.settings, self.on_setting_added)

        # Undo/Redoステータス監視
        self.sub_undo_status(str(self.store.state.counter), self.on_counter_undo_status)
        self.sub_undo_status(str(self.store.state.todos), self.on_todos_undo_status)

    def on_counter_undo_status(
        self, can_undo: bool, can_redo: bool, undo_count: int, redo_count: int
    ):
        """カウンターのUndo/Redoステータス変化ハンドラー"""
        self.counter_undo_status = {
            "can_undo": can_undo,
            "can_redo": can_redo,
            "undo_count": undo_count,
            "redo_count": redo_count,
        }
        self.refresh_from_state()

    def on_todos_undo_status(
        self, can_undo: bool, can_redo: bool, undo_count: int, redo_count: int
    ):
        """TodoリストのUndo/Redoステータス変化ハンドラー"""
        self.todos_undo_status = {
            "can_undo": can_undo,
            "can_redo": can_redo,
            "undo_count": undo_count,
            "redo_count": redo_count,
        }
        self.refresh_from_state()

    def refresh_from_state(self):
        state = self.store.get_current_state()
        # Containerで状態から必要な値を抽出してPresentationalに渡す
        completed_todos = sum(1 for t in state.todos if t.completed)
        total_todos = len(state.todos)

        self.stats_view.update_stats(
            counter=state.counter,
            total_clicks=state.total_clicks,
            total_todos=total_todos,
            completed_todos=completed_todos,
            settings_count=len(state.settings),
            current_view=state.current_view,
            counter_undo_status=self.counter_undo_status,
            todos_undo_status=self.todos_undo_status,
        )

    def on_setting_added(self, key: str, value: str):
        messagebox.showinfo("設定追加", f"設定追加: {key} = {value}")

    def close_all(self):
        # pub_close_all_subwindows使用
        self.pub_close_all_subwindows()

    def delete_proc(self):
        try:
            # pub_delete_processor使用
            self.pub_delete_processor("dummy")
            messagebox.showinfo("成功", "プロセッサーを削除しました")
        except KeyError:
            messagebox.showerror("エラー", "プロセッサーが見つかりません")


# =============================================================================
# サブウィンドウ
# =============================================================================


class SubWindow(ContainerComponentTk[AppState]):
    def setup_ui(self):
        tk.Label(self, text="🔢 サブウィンドウ", font=("Arial", 14)).pack(pady=10)

        self.value_label = tk.Label(self, text="0", font=("Arial", 20))
        self.value_label.pack(pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="+1", command=self.increment).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btn_frame, text="+5", command=lambda: self.add_value(5)).pack(
            side=tk.LEFT, padx=5
        )

        tk.Button(self, text="閉じる", command=self.close_window).pack(pady=10)

    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.counter, self.on_counter_changed)

    def refresh_from_state(self):
        state = self.store.get_current_state()
        self.value_label.config(text=str(state.counter))

    def on_counter_changed(self, old_value, new_value):
        self.value_label.config(text=str(new_value))

    def increment(self):
        self.publish(AppTopic.INCREMENT)

    def add_value(self, value: int):
        state = self.store.get_current_state()
        new_value = state.counter + value
        self.pub_update_state(self.store.state.counter, new_value)
        self.pub_update_state(self.store.state.total_clicks, state.total_clicks + 1)

    def close_window(self):
        # pub_close_subwindow使用
        self.pub_close_subwindow(self.kwargs["win_id"])


# =============================================================================
# プロセッサー
# =============================================================================


class MainProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe(AppTopic.INCREMENT, self.handle_increment)
        self.subscribe(AppTopic.RESET, self.handle_reset)

    def handle_increment(self):
        state = self.store.get_current_state()
        new_counter = state.counter + 1
        new_total = state.total_clicks + 1

        self.pub_update_state(self.store.state.counter, new_counter)
        self.pub_update_state(self.store.state.total_clicks, new_total)

        # マイルストーン判定
        if new_counter % 10 == 0:
            self.publish(AppTopic.MILESTONE, value=new_counter)

    def handle_reset(self):
        self.pub_update_state(self.store.state.counter, 0)


class DummyProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        print("DummyProcessor: 初期化されました")


# =============================================================================
# メインアプリケーション
# =============================================================================

if __name__ == "__main__":
    app = TkApplication(AppState, title="🎯 PubSubTk Demo", geometry="800x600")

    # メインプロセッサー登録
    app.pub_register_processor(MainProcessor)

    # テンプレート設定
    app.set_template(AppTemplate)

    # 各スロットにコンテナ配置
    app.pub_switch_slot("navbar", NavbarContainer)
    app.pub_switch_slot("main", MainContainer)  # 初期画面
    app.pub_switch_slot("sidebar", SidebarContainer)

    # 起動
    app.run(use_async=True)
