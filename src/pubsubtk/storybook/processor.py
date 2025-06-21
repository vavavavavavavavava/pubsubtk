# storybook/processor.py - StorybookProcessor
"""PubSubTk Processor: Story 選択・レイアウト切替を管理。"""

from pubsubtk import ProcessorBase
from pubsubtk.storybook.state import StorybookState
from pubsubtk.storybook.topic import SBTopic


class StorybookProcessor(ProcessorBase[StorybookState]):
    """Storybook 用のビジネスロジックをまとめる Processor"""

    def setup_subscriptions(self):
        self.subscribe(SBTopic.SELECT_STORY, self.select_story)
        self.subscribe(SBTopic.TOGGLE_CANVAS, self.toggle_canvas)

    def select_story(self, story_id: str) -> None:
        self.pub_update_state(str(self.store.state.active_story_id), story_id)

    def toggle_canvas(self) -> None:
        cur = self.store.get_current_state().layout_mode
        new_mode = "fullscreen" if cur == "normal" else "normal"
        self.pub_update_state(str(self.store.state.layout_mode), new_mode)
