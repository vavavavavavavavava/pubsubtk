import tkinter as tk
from typing import List, Optional

from pydantic import BaseModel

from pubsubtk import PresentationalComponentTk


class TaskItem(BaseModel):
    id: int
    title: str
    completed: bool = False


class TaskItemView(PresentationalComponentTk):
    def setup_ui(self):
        self.var_completed = tk.BooleanVar()

        self.check = tk.Checkbutton(
            self, variable=self.var_completed, command=self._on_toggle
        )
        self.check.pack(side=tk.LEFT)

        self.label = tk.Label(self, text="", width=20, anchor="w")
        self.label.pack(side=tk.LEFT, padx=5)

        self.delete_btn = tk.Button(self, text="削除", command=self._on_delete)
        self.delete_btn.pack(side=tk.RIGHT)

        # 選択状態の表示用
        self.selected_indicator = tk.Label(self, text="→", width=2)
        self.selected_indicator.pack(side=tk.LEFT)
        self.is_selected = False

    def update_data(self, task: TaskItem, is_selected: bool = False):
        self.task_id = task.id
        self.var_completed.set(task.completed)
        self.label.config(text=task.title)

        # 選択状態の更新
        self.is_selected = is_selected
        if is_selected:
            self.selected_indicator.config(text="→")
            self.config(background="#e0e0ff")
        else:
            self.selected_indicator.config(text="")
            self.config(background="SystemButtonFace")

    def _on_toggle(self):
        self.trigger_event("toggle", task_id=self.task_id)

    def _on_delete(self):
        self.trigger_event("delete", task_id=self.task_id)


class TaskListView(PresentationalComponentTk):
    def setup_ui(self):
        self.frame = tk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.task_views = []

    def update_data(self, tasks: List[TaskItem], selected_id: Optional[int] = None):
        # 既存のタスクビューをクリア
        for view in self.task_views:
            view.destroy()
        self.task_views = []

        # タスクごとに新しいビューを作成
        for task in tasks:
            is_selected = selected_id == task.id
            view = TaskItemView(self.frame)
            view.update_data(task, is_selected)
            view.pack(fill=tk.X, pady=2)

            # イベントハンドラを登録
            view.register_handler(
                "toggle", lambda task_id: self.trigger_event("toggle", task_id=task_id)
            )
            view.register_handler(
                "delete", lambda task_id: self.trigger_event("delete", task_id=task_id)
            )

            # クリック時のイベント
            view.bind(
                "<Button-1>",
                lambda e, tid=task.id: self.trigger_event("select", task_id=tid),
            )

            self.task_views.append(view)
