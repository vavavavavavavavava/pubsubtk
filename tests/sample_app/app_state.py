from typing import List, Optional

from pydantic import BaseModel


class TaskItem(BaseModel):
    id: int
    title: str
    completed: bool = False


class AppState(BaseModel):
    tasks: List[TaskItem] = []
    counter: int = 0
    selected_task_id: Optional[int] = None
