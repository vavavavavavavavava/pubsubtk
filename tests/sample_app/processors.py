from pubsubtk import ProcessorBase

from app_state import AppState, TaskItem
from app_topics import TaskTopic


class TaskProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe(TaskTopic.ADD_TASK, self.on_add_task)
        self.subscribe(TaskTopic.TOGGLE_TASK, self.on_toggle_task)
        self.subscribe(TaskTopic.SELECT_TASK, self.on_select_task)
        self.subscribe(TaskTopic.DELETE_TASK, self.on_delete_task)

    def on_add_task(self, title: str):
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
        self.store.update_state(self.store.state.selected_task_id, task_id)

    def on_delete_task(self, task_id: int):
        state = self.store.get_current_state()

        # 特定IDのタスクを除外した新しいリストを作成
        updated_tasks = [task for task in state.tasks if task.id != task_id]
        self.store.update_state(self.store.state.tasks, updated_tasks)
