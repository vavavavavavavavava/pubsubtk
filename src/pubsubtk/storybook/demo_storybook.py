# demo_storybook.py - Storybook 起動サンプル
"""最小限の PubSubTk Storybook デモアプリ。"""

import tkinter as tk
from tkinter import ttk

from pubsubtk.core.pubsub_base import enable_pubsub_debug_logging
from pubsubtk.storybook import StorybookApplication, story
from pubsubtk.storybook.core.context import StoryContext


# ------------------------------------------------------------------ #
# Story 定義例
@story("UI.Label.Primary")
def label_primary(ctx):
    """動的テキスト & サイズのラベル"""
    text = ctx.knob("text", str, "Hello Storybook", desc="表示するテキスト")
    size = ctx.knob("size", int, 24, desc="フォントサイズ", range_=(8, 64))
    color = ctx.knob(
        "color",
        str,
        "black",
        desc="文字色",
        choices=["black", "red", "blue", "green", "purple"],
    )

    lbl = tk.Label(
        ctx.parent, text=text.value, font=("Arial", size.value), fg=color.value
    )
    return lbl


@story("UI.Button.Danger")
def button_danger(ctx: StoryContext):
    """危険アクション用ボタン"""
    text = ctx.knob("caption", str, "Delete", desc="ボタンテキスト")
    enabled = ctx.knob("enabled", bool, True, desc="有効/無効")
    width = ctx.knob("width", int, 12, desc="ボタン幅", range_=(8, 30))

    btn = tk.Button(
        ctx.parent,
        text=text.value,
        bg="red",
        fg="white",
        width=width.value,
        state="normal" if enabled.value else "disabled",
    )
    return btn


@story("UI.Entry.Search")
def entry_search(ctx: StoryContext):
    """検索入力フィールド"""
    placeholder = ctx.knob("placeholder", str, "Search...", desc="プレースホルダー")
    width = ctx.knob("width", int, 30, desc="幅", range_=(10, 100))
    readonly = ctx.knob("readonly", bool, False, desc="読み取り専用")

    entry = tk.Entry(
        ctx.parent, width=width.value, state="readonly" if readonly.value else "normal"
    )
    entry.insert(0, placeholder.value)
    return entry


@story("UI.Text.Multiline")
def text_multiline(ctx: StoryContext):
    """複数行テキストエリア"""
    content = ctx.knob(
        "content",
        str,
        "This is a multiline\ntext area example.\n\nYou can edit this content!",
        desc="テキスト内容",
        multiline=True,
    )
    height = ctx.knob("height", int, 8, desc="行数", range_=(3, 20))
    width = ctx.knob("width", int, 40, desc="列数", range_=(20, 100))

    text_widget = tk.Text(
        ctx.parent, height=height.value, width=width.value, wrap=tk.WORD
    )
    text_widget.insert("1.0", content.value)
    return text_widget


@story("TTK.Button.Themed")
def ttk_button_themed(ctx: StoryContext):
    """テーマ対応ボタン"""
    text = ctx.knob("text", str, "Themed Button", desc="ボタンテキスト")
    state = ctx.knob(
        "state", str, "normal", desc="状態", choices=["normal", "disabled", "pressed"]
    )
    width = ctx.knob("width", int, 15, desc="幅", range_=(10, 30))

    btn = ttk.Button(ctx.parent, text=text.value, width=width.value)
    btn.configure(state=state.value)
    return btn


@story("TTK.Progress.Bar")
def ttk_progress_bar(ctx: StoryContext):
    """プログレスバー"""
    value = ctx.knob("value", int, 50, desc="進捗値", range_=(0, 100))
    mode = ctx.knob(
        "mode",
        str,
        "determinate",
        desc="モード",
        choices=["determinate", "indeterminate"],
    )
    length = ctx.knob("length", int, 300, desc="長さ", range_=(100, 500))

    progress = ttk.Progressbar(
        ctx.parent, mode=mode.value, length=length.value, value=value.value
    )
    return progress


# ------------------------------------------------------------------ #
# 起動エントリ
if __name__ == "__main__":
    # 自動検索版を使う場合
    # discover_stories("src")  # src ディレクトリから自動検索
    enable_pubsub_debug_logging()
    # 手動版（上記のstory定義が既にここで実行されているため自動登録済み）
    app = StorybookApplication(
        title="PubSubTk Storybook Demo",
        geometry="1400x900",
        theme="arc",  # clam, alt, default, classic等も選択可能
    )
    app.run()
