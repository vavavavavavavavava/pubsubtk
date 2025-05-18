import tkinter as tk

from app_state import AppState
from app_topics import TaskTopic
from ui.components import TaskListView

from pubsubtk import ContainerComponentTk


class TaskListContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
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

    def setup_subscriptions(self):
        # 状態変更の購読
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
        state = self.store.get_current_state()
        self.task_list.update_data(state.tasks, state.selected_task_id)

    def _on_added(self, item, index):
        # 状態から最新のタスクリストを取得して表示を更新
        self.refresh_from_state()

    def _on_changed(self, old_value, new_value):
        # 選択状態が変わったので表示を更新
        self.refresh_from_state()

    def _on_add(self, event=None):
        task_title = self.entry.get().strip()
        if task_title:
            # TaskTopicメッセージを送信
            self.publish(TaskTopic.ADD_TASK, title=task_title)
            self.entry.delete(0, tk.END)  # 入力欄をクリア

    def _on_toggle_task(self, task_id):
        self.publish(TaskTopic.TOGGLE_TASK, task_id=task_id)

    def _on_delete_task(self, task_id):
        self.publish(TaskTopic.DELETE_TASK, task_id=task_id)

    def _on_select_task(self, task_id):
        self.publish(TaskTopic.SELECT_TASK, task_id=task_id)
