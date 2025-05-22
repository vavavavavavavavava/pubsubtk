import tkinter as tk

from app_state import AppState

from pubsubtk import ContainerComponentTk
from pubsubtk.store.store import Store


class TaskDetailWindow(ContainerComponentTk[AppState]):
    """
    タスク詳細ウィンドウのPubSub連携コンテナ。

    タスクのタイトル編集と保存を行うサブウィンドウを提供します。
    アプリケーション状態（AppState）と連携し、状態の購読・反映を行います。
    """

    def __init__(self, parent, store: Store[AppState], task_id: int, on_save):
        """
        TaskDetailWindowの初期化。

        Args:
            parent: 親ウィジェット。
            store: アプリケーション状態を管理するStoreインスタンス。
            task_id: 編集対象タスクのID。
            on_save: 保存時に呼び出されるコールバック関数。引数は(task_id, new_title)。
        """
        self.task_id = task_id
        self.on_save = on_save
        self.title_var = tk.StringVar()
        super().__init__(parent, store)

    def setup_subscriptions(self):
        return super().setup_subscriptions()

    def setup_ui(self):
        """
        ウィジェットの構築とレイアウトを行います。
        """
        tk.Label(self, text="タスクタイトル:").pack(pady=10)
        self.title_entry = tk.Entry(self, textvariable=self.title_var, width=40)
        self.title_entry.pack(pady=5)

        self.save_button = tk.Button(self, text="保存", command=self.save_task)
        self.save_button.pack(pady=10)

        self.cancel_button = tk.Button(self, text="キャンセル", command=self.destroy)
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
        if new_title:
            self.on_save(self.task_id, new_title)
            self.destroy()
