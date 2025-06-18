# storybook/processor.py - StorybookProcessor
"""PubSubTk Processor: Story 選択・レイアウト切替・Knob変更を管理。"""

from typing import Any

from pubsubtk import ProcessorBase

from .state import StorybookState
from .topic import SBTopic


class StorybookProcessor(ProcessorBase[StorybookState]):
    """Storybook 用のビジネスロジックをまとめる Processor"""

    def setup_subscriptions(self):
        self.subscribe(SBTopic.SELECT_STORY, self.select_story)
        self.subscribe(SBTopic.KNOB_CHANGED, self.knob_changed)
        self.subscribe(SBTopic.TOGGLE_CANVAS, self.toggle_canvas)

    def select_story(self, story_id: str) -> None:
        self.pub_update_state(str(self.store.state.active_story_id), story_id)
        self.pub_update_state(str(self.store.state.knob_values), {})

    def knob_changed(self, name: str, value: Any) -> None:
        kv = self.store.get_current_state().knob_values | {name: value}
        self.pub_update_state(str(self.store.state.knob_values), kv)

    def toggle_canvas(self) -> None:
        cur = self.store.get_current_state().layout_mode
        new_mode = "fullscreen" if cur == "normal" else "normal"
        self.pub_update_state(str(self.store.state.layout_mode), new_mode)
