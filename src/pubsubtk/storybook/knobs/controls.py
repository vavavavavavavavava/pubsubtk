# storybook/knob/knob_controls.py
"""個別のKnob UI制御ウィジェット"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from .types import KnobValue


class KnobControlBase:
    """Knob制御ウィジェットの基底クラス"""

    def __init__(
        self, parent: tk.Widget, knob_value: KnobValue, on_change: Callable[[Any], None]
    ):
        self.parent = parent
        self.knob_value = knob_value
        self.on_change = on_change
        self.frame = ttk.Frame(parent)
        self._setup_ui()

    def _setup_ui(self):
        """UIセットアップ（サブクラスで実装）"""
        raise NotImplementedError

    def pack(self, **kwargs):
        """フレームをpack"""
        self.frame.pack(**kwargs)


class TextKnobControl(KnobControlBase):
    """テキスト入力Knob"""

    def __init__(self, parent, knob_value, on_change):
        super().__init__(parent, knob_value, on_change)
        self._debounce_timer = None
        self._debounce_delay = 300  # 300ms

    def _setup_ui(self):
        spec = self.knob_value.spec

        # ラベル
        ttk.Label(self.frame, text=f"{spec.name}:", width=15, anchor="w").pack(
            side="left", padx=(0, 5)
        )

        # 入力フィールド
        if spec.multiline:
            self.widget = tk.Text(self.frame, height=3, width=30)
            self.widget.insert("1.0", str(self.knob_value.value))
            self.widget.bind("<KeyRelease>", self._on_text_change)
        else:
            self.var = tk.StringVar(value=str(self.knob_value.value))
            self.widget = ttk.Entry(self.frame, textvariable=self.var, width=30)
            self.var.trace_add("write", self._on_var_change)

        self.widget.pack(side="left", fill="x", expand=True)

    def _on_var_change(self, *args):
        """変数変更時（デバウンス付き）"""
        new_value = self.var.get()
        self.knob_value.value = new_value
        
        # 既存のタイマーをキャンセル
        if self._debounce_timer:
            self.frame.after_cancel(self._debounce_timer)
        
        # 新しいタイマーを設定
        self._debounce_timer = self.frame.after(
            self._debounce_delay, 
            lambda: self.on_change(new_value)
        )

    def _on_text_change(self, event):
        """テキスト変更時（デバウンス付き）"""
        new_value = self.widget.get("1.0", "end-1c")
        self.knob_value.value = new_value
        
        # 既存のタイマーをキャンセル
        if self._debounce_timer:
            self.frame.after_cancel(self._debounce_timer)
        
        # 新しいタイマーを設定
        self._debounce_timer = self.frame.after(
            self._debounce_delay, 
            lambda: self.on_change(new_value)
        )


class NumberKnobControl(KnobControlBase):
    """数値入力Knob（スライダー付き）"""

    def __init__(self, parent, knob_value, on_change):
        super().__init__(parent, knob_value, on_change)
        self._debounce_timer = None
        self._debounce_delay = 300  # 300ms

    def _setup_ui(self):
        spec = self.knob_value.spec

        # ラベル
        ttk.Label(self.frame, text=f"{spec.name}:", width=15, anchor="w").pack(
            side="left", padx=(0, 5)
        )

        # 数値入力
        self.var = tk.StringVar(value=str(self.knob_value.value))
        entry = ttk.Entry(self.frame, textvariable=self.var, width=8)
        entry.pack(side="left", padx=(0, 5))
        self.var.trace_add("write", self._on_entry_change)

        # スライダー（range指定時）
        if spec.range_:
            from_, to = spec.range_
            self.scale_var = tk.DoubleVar(value=float(self.knob_value.value))
            scale = ttk.Scale(
                self.frame,
                from_=from_,
                to=to,
                variable=self.scale_var,
                orient="horizontal",
                length=150,
            )
            scale.pack(side="left", fill="x", expand=True)
            self.scale_var.trace_add("write", self._on_scale_change)

    def _on_entry_change(self, *args):
        """入力フィールド変更時"""
        try:
            new_value = self.knob_value.spec.type_(self.var.get())
            self.knob_value.value = new_value
            if hasattr(self, "scale_var"):
                self.scale_var.set(float(new_value))
            self.on_change(new_value)
        except (ValueError, TypeError):
            pass

    def _on_scale_change(self, *args):
        """スライダー変更時（デバウンス付き）"""
        new_value = self.knob_value.spec.type_(self.scale_var.get())
        self.var.set(str(new_value))
        self.knob_value.value = new_value
        
        # 既存のタイマーをキャンセル
        if self._debounce_timer:
            self.frame.after_cancel(self._debounce_timer)
        
        # 新しいタイマーを設定
        self._debounce_timer = self.frame.after(
            self._debounce_delay, 
            lambda: self.on_change(new_value)
        )


class BooleanKnobControl(KnobControlBase):
    """ブール値チェックボックス"""

    def __init__(self, parent, knob_value, on_change):
        super().__init__(parent, knob_value, on_change)
        self._debounce_timer = None
        self._debounce_delay = 100  # 100ms (shorter for boolean)

    def _setup_ui(self):
        spec = self.knob_value.spec

        # チェックボックス
        self.var = tk.BooleanVar(value=self.knob_value.value)
        checkbox = ttk.Checkbutton(self.frame, text=spec.name, variable=self.var)
        checkbox.pack(side="left", anchor="w")
        self.var.trace_add("write", self._on_change_callback)

    def _on_change_callback(self, *args):
        """チェックボックス変更時（デバウンス付き）"""
        new_value = self.var.get()
        self.knob_value.value = new_value
        
        # 既存のタイマーをキャンセル
        if self._debounce_timer:
            self.frame.after_cancel(self._debounce_timer)
        
        # 新しいタイマーを設定
        self._debounce_timer = self.frame.after(
            self._debounce_delay, 
            lambda: self.on_change(new_value)
        )


class SelectKnobControl(KnobControlBase):
    """選択肢ドロップダウン"""

    def __init__(self, parent, knob_value, on_change):
        super().__init__(parent, knob_value, on_change)
        self._debounce_timer = None
        self._debounce_delay = 100  # 100ms (shorter for selection)

    def _setup_ui(self):
        spec = self.knob_value.spec

        # ラベル
        ttk.Label(self.frame, text=f"{spec.name}:", width=15, anchor="w").pack(
            side="left", padx=(0, 5)
        )

        # ドロップダウン
        self.var = tk.StringVar(value=str(self.knob_value.value))
        combo = ttk.Combobox(
            self.frame,
            textvariable=self.var,
            values=spec.choices,
            state="readonly",
            width=20,
        )
        combo.pack(side="left", fill="x", expand=True)
        self.var.trace_add("write", self._on_change_callback)

    def _on_change_callback(self, *args):
        """ドロップダウン変更時（デバウンス付き）"""
        new_value = self.var.get()
        self.knob_value.value = new_value
        
        # 既存のタイマーをキャンセル
        if self._debounce_timer:
            self.frame.after_cancel(self._debounce_timer)
        
        # 新しいタイマーを設定
        self._debounce_timer = self.frame.after(
            self._debounce_delay, 
            lambda: self.on_change(new_value)
        )


def create_knob_control(
    parent: tk.Widget, knob_value: KnobValue, on_change: Callable[[Any], None]
) -> KnobControlBase:
    """KnobSpecに応じた適切なコントロールを作成"""
    spec = knob_value.spec

    if spec.type_ == bool:
        return BooleanKnobControl(parent, knob_value, on_change)
    elif spec.choices:
        return SelectKnobControl(parent, knob_value, on_change)
    elif spec.type_ in (int, float):
        return NumberKnobControl(parent, knob_value, on_change)
    else:  # str or others
        return TextKnobControl(parent, knob_value, on_change)
