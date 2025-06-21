# demo_storybook.py - Storybook 起動サンプル
"""最小限の PubSubTk Storybook デモアプリ。"""

import tkinter as tk
from tkinter import ttk

from pubsubtk.core.pubsub_base import enable_pubsub_debug_logging
from pubsubtk.storybook import StorybookApplication, story
from pubsubtk.storybook.context import StoryContext


# ------------------------------------------------------------------ #
# Story 定義例
@story("UI.Label.Primary")
def label_primary(ctx):
    """シンプルなラベル"""
    lbl = tk.Label(
        ctx.parent, text="Hello Storybook", font=("Arial", 24), fg="black"
    )
    return lbl


@story("UI.Button.Danger")
def button_danger(ctx: StoryContext):
    """危険アクション用ボタン"""
    btn = tk.Button(
        ctx.parent,
        text="Delete",
        bg="red",
        fg="white",
        width=12,
    )
    return btn


@story("UI.Entry.Search")
def entry_search(ctx: StoryContext):
    """検索入力フィールド"""
    entry = tk.Entry(ctx.parent, width=30)
    entry.insert(0, "Search...")
    return entry


@story("UI.Text.Multiline")
def text_multiline(ctx: StoryContext):
    """複数行テキストエリア"""
    text_widget = tk.Text(ctx.parent, height=8, width=40, wrap=tk.WORD)
    text_widget.insert("1.0", "This is a multiline\ntext area example.\n\nYou can edit this content!")
    return text_widget


@story("TTK.Button.Themed")
def ttk_button_themed(ctx: StoryContext):
    """テーマ対応ボタン"""
    btn = ttk.Button(ctx.parent, text="Themed Button", width=15)
    return btn


@story("TTK.Progress.Bar")
def ttk_progress_bar(ctx: StoryContext):
    """プログレスバー"""
    progress = ttk.Progressbar(ctx.parent, mode="determinate", length=300, value=50)
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
