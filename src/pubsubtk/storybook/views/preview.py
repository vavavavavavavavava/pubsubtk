# storybook/views/preview.py - PreviewFrame
"""選択された Story を実際に描画するプレビューフレーム。"""

import tkinter as tk
from tkinter import ttk

from pubsubtk import ContainerComponentTtk
from pubsubtk.storybook.context import StoryContext
from pubsubtk.storybook.registry import StoryRegistry
from pubsubtk.storybook.state import StorybookState


class PreviewFrame(ContainerComponentTtk[StorybookState]):
    """中央のプレビューエリア（テーマ対応）"""

    def setup_ui(self):
        # 初期表示用の中央配置フレーム
        self.center_frame = ttk.Frame(self)
        self.center_frame.pack(expand=True)

        # アイコンと説明文
        icon_label = ttk.Label(self.center_frame, text="🎨", font=("", 48))
        icon_label.pack(pady=(20, 10))

        self.label = ttk.Label(
            self.center_frame,
            text="Select a story from the sidebar",
            font=("", 12),
            foreground="gray",
        )
        self.label.pack()

    def setup_subscriptions(self):
        self.sub_for_refresh(str(self.store.state.active_story_id), self._refresh)
        # Knob変更時の再描画を購読
        self.subscribe("storybook.knob.changed", self._on_knob_changed)

    def refresh_from_state(self):
        # 初期化時の処理
        self._refresh()

    def _refresh(self):
        # 既存ウィジェット破棄
        for w in self.winfo_children():
            w.destroy()

        story_id = self.store.get_current_state().active_story_id
        if not story_id:
            self._show_empty_state()
            # 空のストーリー時はKnobPanelをクリア
            self.publish("storybook.knobs.update", knob_values={})
            return

        stories = [m for m in StoryRegistry.list() if m.id == story_id]
        if not stories:
            self._show_error_state("Story not found")
            return

        meta = stories[0]

        try:

            # コンテンツフレーム作成
            content_frame = ttk.Frame(self)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Story情報ヘッダー
            info_frame = ttk.Frame(content_frame)
            info_frame.pack(fill=tk.X, pady=(0, 10))

            path_text = " > ".join(meta.path + [meta.title])
            ttk.Label(
                info_frame, text=path_text, font=("", 10), foreground="gray"
            ).pack(side=tk.LEFT)

            # 区切り線
            ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(
                fill=tk.X, pady=(0, 10)
            )

            # Story実行エリア
            story_frame = ttk.Frame(content_frame)
            story_frame.pack(fill=tk.BOTH, expand=True)

            ctx = StoryContext(parent=story_frame)
            ctx.set_publish_callback(self.publish)
            ctx.set_story_id(story_id)  # ストーリーIDを設定して値を永続化

            widget = meta.factory(ctx)
            widget.pack(fill=tk.BOTH, expand=True)
            
            # KnobPanelにKnob情報を送信
            self.publish("storybook.knobs.update", knob_values=ctx.knob_values)


        except Exception as e:
            self._show_error_state(f"Error rendering story: {str(e)}")

    def _show_empty_state(self):
        """空の状態を表示"""
        center_frame = ttk.Frame(self)
        center_frame.pack(expand=True)

        icon_label = ttk.Label(center_frame, text="🎨", font=("", 48))
        icon_label.pack(pady=(20, 10))

        ttk.Label(
            center_frame,
            text="Select a story from the sidebar",
            font=("", 12),
            foreground="gray",
        ).pack()

    def _show_error_state(self, message: str):
        """エラー状態を表示"""
        center_frame = ttk.Frame(self)
        center_frame.pack(expand=True)

        icon_label = ttk.Label(center_frame, text="⚠️", font=("", 48))
        icon_label.pack(pady=(20, 10))

        ttk.Label(center_frame, text=message, font=("", 12), foreground="red").pack()
    
    def _refresh_story_only(self):
        """Knob値変更時のstoryのみ再描画（KnobUIは更新しない）"""
        # 既存ウィジェット破棄
        for w in self.winfo_children():
            w.destroy()

        story_id = self.store.get_current_state().active_story_id
        if not story_id:
            self._show_empty_state()
            return

        stories = [m for m in StoryRegistry.list() if m.id == story_id]
        if not stories:
            self._show_error_state("Story not found")
            return

        meta = stories[0]

        try:
            # コンテンツフレーム作成
            content_frame = ttk.Frame(self)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Story情報ヘッダー
            info_frame = ttk.Frame(content_frame)
            info_frame.pack(fill=tk.X, pady=(0, 10))

            path_text = " > ".join(meta.path + [meta.title])
            ttk.Label(
                info_frame, text=path_text, font=("", 10), foreground="gray"
            ).pack(side=tk.LEFT)

            # 区切り線
            ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(
                fill=tk.X, pady=(0, 10)
            )

            # Story実行エリア
            story_frame = ttk.Frame(content_frame)
            story_frame.pack(fill=tk.BOTH, expand=True)

            ctx = StoryContext(parent=story_frame)
            ctx.set_publish_callback(self.publish)
            ctx.set_story_id(story_id)  # ストーリーIDを設定して値を永続化

            widget = meta.factory(ctx)
            widget.pack(fill=tk.BOTH, expand=True)
            
            # 注意: KnobPanelには通知しない（knob値変更時はUI再構築を避ける）

        except Exception as e:
            self._show_error_state(f"Error rendering story: {str(e)}")
    
    def _on_knob_changed(self, knob_name: str, value):
        """Knob値変更時のコールバック（ストーリー再描画）"""
        # knob値変更時はstoryのみ更新、KnobUIは再構築しない
        self._refresh_story_only()

