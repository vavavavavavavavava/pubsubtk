from app_state import AppState
from processors import TaskProcessor
from ui.containers.task_list_container import TaskListContainer

from pubsubtk import (
    TkApplication,
)


def main():
    # アプリケーションのインスタンスを作成し、状態クラスを渡す
    app = TkApplication(state_cls=AppState)

    # TaskProcessorをアプリケーションに登録
    app.register_processor(TaskProcessor)

    # アプリケーション開始時に表示するコンテナを設定
    app.switch_container(TaskListContainer)

    # アプリケーションのメインループを開始
    app.run()


if __name__ == "__main__":
    main()
