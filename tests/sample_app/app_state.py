from typing import List, Optional

from pydantic import BaseModel


class TaskItem(BaseModel):
    """
    タスク1件分の状態を表すモデル。
    - id: タスクの一意なID
    - title: タスクのタイトル
    - completed: 完了フラグ
    """

    id: int
    title: str
    completed: bool = False


class AppState(BaseModel):
    """
    アプリ全体の状態を保持するモデル。
    - tasks: タスク一覧
    - counter: タスクID発番用カウンタ
    - selected_task_id: 現在選択中のタスクID
    """

    tasks: List[TaskItem] = []
    counter: int = 0
    selected_task_id: Optional[int] = None
