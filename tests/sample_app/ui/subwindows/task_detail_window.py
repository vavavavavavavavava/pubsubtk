import tkinter as tk

from app_state import AppState
from app_topics import TaskTopic

from pubsubtk import ContainerComponentTk


class TaskDetailWindow(ContainerComponentTk[AppState]):
    """
    タスク詳細ウィンドウのPubSub連携コンテナ。

    タスクのタイトル編集と保存を行うサブウィンドウを提供します。
    アプリケーション状態（AppState）と連携し、状態の購読・反映を行います。
    """

    def setup_subscriptions(self):
        return super().setup_subscriptions()

    def setup_ui(self):
        """
        ウィジェットの構築とレイアウトを行います。
        """
        self.win_id = self.kwargs.get(
            "win_id"
        )  # subwindowとして開いた場合はkwargsの"win_id"がデフォルトで取得できます。
        self.task_id = self.kwargs.get("task_id")
        self.title_var = tk.StringVar()

        tk.Label(self, text="タスクタイトル:").pack(pady=10)
        self.title_entry = tk.Entry(self, textvariable=self.title_var, width=40)
        self.title_entry.pack(pady=5)

        self.save_button = tk.Button(self, text="保存", command=self.save_task)
        self.save_button.pack(pady=10)

        self.cancel_button = tk.Button(
            self, text="キャンセル", command=self.close_window
        )
        self.cancel_button.pack(pady=5)

    def refresh_from_state(self):
        """
        アプリケーション状態から該当タスクのタイトルを取得し、UIに反映します。
        """
        state = self.store.get_current_state()
        task = next((t for t in state.tasks if t.id == self.task_id), None)
        if task:
            self.title_var.set(task.title)
        else:
            self.title_var.set("")

    def save_task(self):
        """
        タスクタイトルを保存し、コールバックを呼び出してウィンドウを閉じます。
        """
        new_title = self.title_var.get().strip()
        # ここでタスク名更新のトピックを発行
        self.publish(TaskTopic.UPDATE_TASK_TITLE, task_id=self.task_id, title=new_title)
        # サブウィンドウを閉じる
        self.close_window()

    def close_window(self):
        """サブウィンドウを閉じる"""
        self.pub_close_subwindow(
            self.win_id
        )  # デフォルトで取得したwin_idで自身が描画されたsubwindowを破壊出来ます。
