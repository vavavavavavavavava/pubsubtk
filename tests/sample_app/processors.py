from app_state import AppState, TaskItem
from app_topics import TaskTopic

from pubsubtk import ProcessorBase


class TaskProcessor(ProcessorBase[AppState]):
    """
    タスク管理に関するビジネスロジックを担当するProcessor。
    UIからのイベント（トピック）を購読し、状態を更新する。
    """

    def setup_subscriptions(self):
        """
        必要なトピックに購読を登録する。
        """
        self.subscribe(TaskTopic.ADD_TASK, self.on_add_task)
        self.subscribe(TaskTopic.TOGGLE_TASK, self.on_toggle_task)
        self.subscribe(TaskTopic.SELECT_TASK, self.on_select_task)
        self.subscribe(TaskTopic.DELETE_TASK, self.on_delete_task)
        self.subscribe(TaskTopic.UPDATE_TASK_TITLE, self.on_update_task_title)  # 追加

    def on_add_task(self, title: str):
        """
        タスク追加イベントのハンドラ。
        新しいIDを発番し、タスクリストに追加する。
        """
        state = self.store.get_current_state()

        # 新しいIDを生成
        next_id = state.counter + 1

        # カウンターを更新
        self.store.update_state(self.store.state.counter, next_id)

        # 新しいタスクを作成
        new_task = TaskItem(id=next_id, title=title)

        # タスクをリストに追加
        self.store.add_to_list(self.store.state.tasks, new_task)

    def on_toggle_task(self, task_id: int):
        """
        タスクの完了状態をトグルするイベントのハンドラ。
        """
        state = self.store.get_current_state()

        for i, task in enumerate(state.tasks):
            if task.id == task_id:
                # タスクの状態を反転
                updated_task = task.model_copy()
                updated_task.completed = not task.completed

                # リストの特定位置を更新
                tasks = state.tasks.copy()
                tasks[i] = updated_task
                self.store.update_state(self.store.state.tasks, tasks)
                break

    def on_select_task(self, task_id: int):
        """
        タスク選択イベントのハンドラ。
        """
        self.store.update_state(self.store.state.selected_task_id, task_id)

    def on_delete_task(self, task_id: int):
        """
        タスク削除イベントのハンドラ。
        """
        state = self.store.get_current_state()

        # 特定IDのタスクを除外した新しいリストを作成
        updated_tasks = [task for task in state.tasks if task.id != task_id]
        self.store.update_state(self.store.state.tasks, updated_tasks)

    def on_update_task_title(self, task_id: int, title: str):
        """
        タスクタイトル更新イベントのハンドラ。
        指定IDのタスクのタイトルを新しい値に変更する。
        """
        state = self.store.get_current_state()
        updated = False
        tasks = []
        for task in state.tasks:
            if task.id == task_id:
                updated_task = task.model_copy()
                updated_task.title = title
                tasks.append(updated_task)
                updated = True
            else:
                tasks.append(task)
        if updated:
            self.store.update_state(self.store.state.tasks, tasks)
