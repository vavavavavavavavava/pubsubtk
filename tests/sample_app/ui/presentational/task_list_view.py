import tkinter as tk
from typing import List, Optional

from app_state import TaskItem

from pubsubtk import PresentationalComponentTk


class TaskItemView(PresentationalComponentTk):
    """
    1つのタスクを表示するプレゼンテーショナルコンポーネント。

    チェックボックス・タイトル・削除ボタン・選択インジケータを持ち、
    UI操作をイベントとして親コンテナに伝える役割を持つ。
    """

    def setup_ui(self):
        """
        タスク表示用UI部品の構築。

        - 完了チェックボックス
        - タイトルラベル
        - 削除ボタン
        - 選択状態インジケータ
        """
        self.var_completed = tk.BooleanVar()

        self.check = tk.Checkbutton(
            self, variable=self.var_completed, command=self._on_toggle
        )
        self.check.pack(side=tk.LEFT)

        self.label = tk.Label(self, text="", width=20, anchor="w")
        self.label.pack(side=tk.LEFT, padx=5)

        self.delete_btn = tk.Button(self, text="削除", command=self._on_delete)
        self.delete_btn.pack(side=tk.RIGHT)

        self.detail_btn = tk.Button(self, text="詳細", command=self._on_detail)
        self.detail_btn.pack(side=tk.RIGHT, padx=2)

        # 選択状態の表示用
        self.selected_indicator = tk.Label(self, text="→", width=2)
        self.selected_indicator.pack(side=tk.LEFT)
        self.is_selected = False

    def update_data(self, task: TaskItem, is_selected: bool = False):
        """
        タスクデータと選択状態を受け取り、UIを更新する。

        Args:
            task (TaskItem): 表示するタスクデータ
            is_selected (bool): このタスクが選択中かどうか
        """
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
        """
        チェックボックス操作時にtoggleイベントを発火。
        """
        self.trigger_event("toggle", task_id=self.task_id)

    def _on_delete(self):
        """
        削除ボタン押下時にdeleteイベントを発火。
        """
        self.trigger_event("delete", task_id=self.task_id)

    def _on_detail(self):
        """
        詳細ボタン押下時にdetailイベントを発火
        """
        self.trigger_event("detail", task_id=self.task_id)


class TaskListView(PresentationalComponentTk):
    """
    タスクリスト全体を表示するプレゼンテーショナルコンポーネント。

    TaskItemViewを並べて表示し、各種イベントを親コンテナに伝える。
    """

    def setup_ui(self):
        """
        タスクリスト表示用のフレームを構築。
        """
        self.frame = tk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.task_views = []

    def update_data(self, tasks: List[TaskItem], selected_id: Optional[int] = None):
        """
        タスクリストと選択IDを受け取り、リスト表示を更新する。

        Args:
            tasks (List[TaskItem]): 表示するタスク一覧
            selected_id (Optional[int]): 選択中タスクのID
        """
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
            view.register_handler(
                "detail", lambda task_id: self.trigger_event("detail", task_id=task_id)
            )

            # クリック時のイベント
            view.bind(
                "<Button-1>",
                lambda e, tid=task.id: self.trigger_event("select", task_id=tid),
            )

            self.task_views.append(view)
