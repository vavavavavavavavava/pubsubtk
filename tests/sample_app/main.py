from app_state import AppState
from processors import TaskProcessor
from ui.containers import TaskListContainer

from pubsubtk import (
    TkApplication,
)


def main():
    app = TkApplication(state_cls=AppState)

    app.register_processor(TaskProcessor)

    app.switch_container(TaskListContainer)

    app.run()


if __name__ == "__main__":
    main()
