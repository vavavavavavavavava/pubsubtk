from typing import List, Optional

from pydantic import BaseModel

from pubsubtk.store.store import create_store, get_store
from pubsubtk.ui.base.container_base import ContainerComponentTk


class TaskItem(BaseModel):
    id: int
    title: str
    completed: bool = False


class AppState(BaseModel):
    tasks: List[TaskItem] = []
    counter: int = 0
    selected_task_id: Optional[int] = None


store = create_store(AppState)
print(store.get_current_state().tasks)
print(store.state.tasks)
print(get_store(AppState).state.tasks)


class App(ContainerComponentTk[AppState]):
    def func(self):
        self.store.state.tasks
