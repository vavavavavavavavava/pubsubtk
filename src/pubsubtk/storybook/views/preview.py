# storybook/views/preview.py - PreviewFrame
"""選択された Story を実際に描画するプレビューフレーム。"""

import tkinter as tk

from pubsubtk import ContainerComponentTk

from ..context import StoryContext
from ..registry import StoryRegistry
from ..state import StorybookState
from ..topic import SBTopic


class PreviewFrame(ContainerComponentTk[StorybookState]):
    """中央のプレビューエリア"""

    def setup_ui(self):
        # 空のレーベルを初期表示
        self.label = tk.Label(self, text="Select a story", fg="gray")
        self.label.pack(expand=True)

    def setup_subscriptions(self):
        self.sub_for_refresh(str(self.store.state.active_story_id), self._refresh)

    def refresh_from_state(self):
        # 初期化時の処理
        self._refresh()

    def _refresh(self):
        # 既存ウィジェット破棄
        for w in self.winfo_children():
            w.destroy()

        story_id = self.store.get_current_state().active_story_id
        if not story_id:
            self.label = tk.Label(self, text="Select a story", fg="gray")
            self.label.pack(expand=True)
            return

        stories = [m for m in StoryRegistry.list() if m.id == story_id]
        if not stories:
            self.label = tk.Label(self, text="Story not found", fg="red")
            self.label.pack(expand=True)
            return

        meta = stories[0]
        ctx = StoryContext(parent=self)
        ctx.set_publish_callback(self.publish)

        widget = meta.factory(ctx)
        widget.pack(fill=tk.BOTH, expand=True)

        # KnobSpec は KnobPanel に通知
        self.publish(SBTopic.KNOB_CHANGED, name="__init__", value=ctx.knob_specs)
