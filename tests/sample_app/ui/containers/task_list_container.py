import tkinter as tk

from app_state import AppState
from app_topics import TaskTopic
from ui.presentational.task_list_view import TaskListView
from ui.subwindows.task_detail_window import TaskDetailWindow

from pubsubtk import ContainerComponentTk


class TaskListContainer(ContainerComponentTk[AppState]):
    """
    タスク一覧画面のコンテナコンポーネント。

    このクラスは、タスクの追加・選択・削除・状態変更などのUIイベントを受け取り、
    適切なトピックを発行してProcessorに処理を委譲します。
    また、状態（AppState）の変化を購読し、UI表示を自動的に更新します。

    UIの構築・イベントハンドラの登録・状態購読のセットアップを担当し、
    プレゼンテーショナルコンポーネント（TaskListView）と状態管理の橋渡しを行います。
    """

    def setup_ui(self):
        """
        UI部品の構築とイベントハンドラの登録。

        - タイトルラベル、タスク追加用の入力フォーム、追加ボタン
        - タスクリスト表示（TaskListView）
        - 各種UIイベント（toggle/delete/select）のハンドラ登録
        """
        self.label = tk.Label(self, text="タスク一覧", font=("", 16))
        self.label.pack(pady=10)

        # 入力フォーム
        self.input_frame = tk.Frame(self)
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.entry = tk.Entry(self.input_frame, width=30)
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<Return>", self._on_add)

        self.add_btn = tk.Button(self.input_frame, text="追加", command=self._on_add)
        self.add_btn.pack(side=tk.LEFT)

        # タスクリスト
        self.task_list = TaskListView(self)
        self.task_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # イベントハンドラの登録
        self.task_list.register_handler("toggle", self._on_toggle_task)
        self.task_list.register_handler("delete", self._on_delete_task)
        self.task_list.register_handler("select", self._on_select_task)
        self.task_list.register_handler("detail", self._on_show_detail)

    def setup_subscriptions(self):
        """
        状態（AppState）の変化を購読し、UIを自動更新する。

        - タスクリスト(tasks)や選択中タスクID(selected_task_id)の変更を監視
        - タスク追加時のイベントも購読
        """
        self.sub_state_changed(
            self.store.state.tasks,
            self._on_changed,
        )
        self.sub_state_changed(
            self.store.state.selected_task_id,
            self._on_changed,
        )
        self.sub_state_added(
            self.store.state.tasks,
            self._on_added,
        )

    def refresh_from_state(self):
        """
        現在の状態（AppState）からタスクリスト表示を更新する。
        """
        state = self.store.get_current_state()
        self.task_list.update_data(state.tasks, state.selected_task_id)

    def _on_added(self, item, index):
        """
        タスクが追加されたときに呼ばれるハンドラ。
        状態から最新のタスクリストを取得して表示を更新する。
        """
        self.refresh_from_state()

    def _on_changed(self, old_value, new_value):
        """
        タスクリストや選択状態が変更されたときに呼ばれるハンドラ。
        表示を更新する。
        """
        self.refresh_from_state()

    def _on_add(self, event=None):
        """
        タスク追加ボタン押下またはEnterキー押下時のハンドラ。

        入力欄のテキストを取得し、空でなければADD_TASKトピックを発行する。
        """
        task_title = self.entry.get().strip()
        if task_title:
            # TaskTopicメッセージを送信
            self.publish(TaskTopic.ADD_TASK, title=task_title)
            self.entry.delete(0, tk.END)  # 入力欄をクリア

    def _on_toggle_task(self, task_id):
        """
        タスクの完了状態トグルイベントをProcessorに伝える。
        """
        self.publish(TaskTopic.TOGGLE_TASK, task_id=task_id)

    def _on_delete_task(self, task_id):
        """
        タスク削除イベントをProcessorに伝える。
        """
        self.publish(TaskTopic.DELETE_TASK, task_id=task_id)

    def _on_select_task(self, task_id):
        """
        タスク選択イベントをProcessorに伝える。
        """
        self.publish(TaskTopic.SELECT_TASK, task_id=task_id)

    def _on_show_detail(self, task_id):
        """
        タスク詳細サブウィンドウを開く。
        """
        # 状態から該当タスクを取得
        state = self.store.get_current_state()
        task = next((t for t in state.tasks if t.id == task_id), None)
        if not task:
            return

        # サブウィンドウを開く（pub_open_subwindowを利用）
        # kwargs辞書で渡す
        self.pub_open_subwindow(
            TaskDetailWindow,
            win_id=f"task_detail_{task_id}",
            kwargs={
                "task_id": task_id,
                "on_save": self._on_save_task_detail,
            },
        )

    def _on_save_task_detail(self, task_id, new_title):
        """
        タスク詳細サブウィンドウで保存されたときの処理。
        """
        # ここでタスク名更新のトピックを発行
        self.publish(TaskTopic.UPDATE_TASK_TITLE, task_id=task_id, title=new_title)
        # サブウィンドウを閉じる
        self.pub_close_subwindow(f"task_detail_{task_id}")
