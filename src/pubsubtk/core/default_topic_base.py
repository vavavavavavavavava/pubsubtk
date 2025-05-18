from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, Type

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.topic.topics import (
    DefaultNavigateTopic,
    DefaultProcessorTopic,
    DefaultUpdateTopic,
)

if TYPE_CHECKING:
    # 型チェック時（mypy や IDE 補完時）のみ読み込む
    from pubsubtk.processor.processor_base import ProcessorBase
    from pubsubtk.ui.base.container_base import ContainerComponentType


class PubSubDefaultTopicBase(PubSubBase):
    def pub_switch_container(
        self,
        cls: ContainerComponentType,
        **kwargs: Any,
    ):
        self.publish(DefaultNavigateTopic.SWITCH_CONTAINER, cls=cls, **kwargs)

    def pub_open_subwindow(
        self,
        cls: ContainerComponentType,
        win_id: Optional[str] = None,
        **kwargs: Any,
    ):
        self.publish(
            DefaultNavigateTopic.OPEN_SUBWINDOW, cls=cls, win_id=win_id, **kwargs
        )

    def pub_close_subwindow(self, win_id: str):
        self.publish(DefaultNavigateTopic.CLOSE_SUBWINDOW, win_id=win_id)

    def pub_close_all_subwindows(self):
        self.publish(DefaultNavigateTopic.CLOSE_ALL_SUBWINDOWS)

    def pub_update_state(self, state_path: str, new_value: Any):
        self.publish(
            DefaultUpdateTopic.UPDATE_STATE,
            state_path=str(state_path),
            new_value=new_value,
        )

    def pub_add_to_list(self, state_path: str, item: Any):
        self.publish(
            DefaultUpdateTopic.ADD_TO_LIST, state_path=str(state_path), item=item
        )

    def pub_registor_processor(
        self, proc: Type[ProcessorBase], name: Optional[str] = None
    ):
        self.publish(DefaultProcessorTopic.REGISTOR_PROCESSOR, proc=proc, name=name)

    def pub_delete_processor(self, name: str):
        self.publish(DefaultProcessorTopic.DELETE_PROCESSOR, name=name)

    def sub_state_changed(self, state_path: str, handler: Callable):
        """handlerは、old_valueとnew_valueを受け取る。

        Args:
            state_path (str): _description_
            handler (Callable): _description_
        """

        self.subscribe(f"{DefaultUpdateTopic.STATE_CHANGED}.{str(state_path)}", handler)

    def sub_state_added(self, state_path: str, handler: Callable):
        """handlerは、itemとindexを受け取る。

        Args:
            state_path (str): _description_
            handler (Callable): _description_
        """
        self.subscribe(f"{DefaultUpdateTopic.STATE_ADDED}.{str(state_path)}", handler)
