# demo_storybook.py - Storybook 起動サンプル
"""最小限の PubSubTk Storybook デモアプリ。"""

import tkinter as tk
from tkinter import ttk

from pubsubtk.storybook import StorybookApplication, story


# ------------------------------------------------------------------ #
# Story 定義例
@story("UI.Label.Primary")
def label_primary(ctx):
    """動的テキスト & サイズのラベル"""
    txt = ctx.knob(
        name="text", type=str, default="Hello Storybook", desc="表示するテキスト"
    )
    size = ctx.knob(
        name="size", type=int, default=24, desc="フォントサイズ", range=(8, 64, 2)
    )
    color = ctx.knob(
        name="color",
        type=str,
        default="black",
        desc="文字色",
        choices=["black", "red", "blue", "green", "purple"],
    )

    lbl = tk.Label(
        ctx.parent, textvariable=txt, font=("Arial", size.get()), fg=color.get()
    )

    # 動的更新
    ctx.on_change(size, lambda v: lbl.config(font=("Arial", v)))
    ctx.on_change(color, lambda v: lbl.config(fg=v))

    return lbl


@story("UI.Button.Danger")
def button_danger(ctx):
    """危険アクション用ボタン"""
    txt = ctx.knob(name="caption", type=str, default="Delete", desc="ボタンテキスト")
    enabled = ctx.knob(name="enabled", type=bool, default=True, desc="有効/無効")
    width = ctx.knob(
        name="width", type=int, default=12, desc="ボタン幅", range=(8, 30, 2)
    )

    btn = tk.Button(
        ctx.parent,
        textvariable=txt,
        bg="red",
        fg="white",
        width=width.get(),
        state="normal" if enabled.get() else "disabled",
    )

    ctx.on_change(enabled, lambda v: btn.config(state="normal" if v else "disabled"))
    ctx.on_change(width, lambda v: btn.config(width=v))

    return btn


@story("UI.Entry.Search")
def entry_search(ctx):
    """検索入力フィールド"""
    placeholder = ctx.knob(
        name="placeholder",
        type=str,
        default="Search...",
        desc="プレースホルダーテキスト",
    )
    width = ctx.knob(
        name="width", type=int, default=30, desc="入力フィールド幅", range=(10, 100, 5)
    )
    readonly = ctx.knob(name="readonly", type=bool, default=False, desc="読み取り専用")

    entry = tk.Entry(
        ctx.parent, width=width.get(), state="readonly" if readonly.get() else "normal"
    )
    entry.insert(0, placeholder.get())

    ctx.on_change(width, lambda v: entry.config(width=v))
    ctx.on_change(readonly, lambda v: entry.config(state="readonly" if v else "normal"))

    return entry


@story("UI.Text.Multiline")
def text_multiline(ctx):
    """複数行テキストエリア"""
    content = ctx.knob(
        name="content",
        type=str,
        default="This is a multiline\ntext area example.\n\nYou can edit this content!",
        desc="テキスト内容",
        multiline=True,
    )
    height = ctx.knob(name="height", type=int, default=8, desc="行数", range=(3, 20, 1))
    width = ctx.knob(
        name="width", type=int, default=40, desc="列数", range=(20, 100, 5)
    )

    text_widget = tk.Text(
        ctx.parent, height=height.get(), width=width.get(), wrap=tk.WORD
    )
    text_widget.insert("1.0", content.get())

    ctx.on_change(height, lambda v: text_widget.config(height=v))
    ctx.on_change(width, lambda v: text_widget.config(width=v))

    return text_widget


@story("TTK.Button.Themed")
def ttk_button_themed(ctx):
    """テーマ対応ボタン"""
    text = ctx.knob(
        name="text", type=str, default="Themed Button", desc="ボタンテキスト"
    )
    state = ctx.knob(
        name="state",
        type=str,
        default="normal",
        desc="ボタン状態",
        choices=["normal", "disabled", "pressed"],
    )
    width = ctx.knob(
        name="width", type=int, default=15, desc="ボタン幅", range=(10, 30, 1)
    )

    btn = ttk.Button(ctx.parent, textvariable=text, width=width.get())
    btn.configure(state=state.get())

    ctx.on_change(state, lambda v: btn.configure(state=v))
    ctx.on_change(width, lambda v: btn.configure(width=v))

    return btn


@story("TTK.Progress.Bar")
def ttk_progress_bar(ctx):
    """プログレスバー"""
    value = ctx.knob(
        name="value", type=int, default=50, desc="進捗値", range=(0, 100, 5)
    )
    mode = ctx.knob(
        name="mode",
        type=str,
        default="determinate",
        desc="モード",
        choices=["determinate", "indeterminate"],
    )
    length = ctx.knob(
        name="length", type=int, default=300, desc="長さ", range=(100, 500, 25)
    )

    progress = ttk.Progressbar(
        ctx.parent, mode=mode.get(), length=length.get(), value=value.get()
    )

    ctx.on_change(value, lambda v: progress.configure(value=v))
    ctx.on_change(mode, lambda v: progress.configure(mode=v))
    ctx.on_change(length, lambda v: progress.configure(length=v))

    return progress


# ------------------------------------------------------------------ #
# 起動エントリ
if __name__ == "__main__":
    # 自動検索版を使う場合
    # discover_stories("src")  # src ディレクトリから自動検索

    # 手動版（上記のstory定義が既にここで実行されているため自動登録済み）
    app = StorybookApplication(
        title="PubSubTk Storybook Demo",
        geometry="1400x900",
        theme="arc",  # clam, alt, default, classic等も選択可能
    )
    app.run()
