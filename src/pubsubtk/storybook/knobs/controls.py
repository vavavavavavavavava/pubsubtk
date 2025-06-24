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
            self._debounce_delay, lambda: self.on_change(new_value)
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
            self._debounce_delay, lambda: self.on_change(new_value)
        )


class NumberKnobControl(KnobControlBase):
    """数値入力Knob（スライダー付き）"""

    def __init__(self, parent, knob_value, on_change):
        super().__init__(parent, knob_value, on_change)
        self._is_sliding = False  # スライダー操作中フラグ
        self._pending_value = None  # 保留中の値

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

        # エントリー変更時のハンドラー（デバウンス付き）
        self._entry_timer = None
        self.var.trace_add("write", self._on_entry_change)

        # スライダー（range指定時）
        if spec.range_:
            from_, to = spec.range_
            self.scale_var = tk.DoubleVar(value=float(self.knob_value.value))
            self.scale = ttk.Scale(
                self.frame,
                from_=from_,
                to=to,
                variable=self.scale_var,
                orient="horizontal",
                length=150,
            )
            self.scale.pack(side="left", fill="x", expand=True)

            # スライダーのイベントバインディング
            self.scale.bind("<ButtonPress-1>", self._on_scale_press)
            self.scale.bind("<ButtonRelease-1>", self._on_scale_release)
            self.scale_var.trace_add("write", self._on_scale_change)

    def _on_entry_change(self, *args):
        """入力フィールド変更時（デバウンス付き）"""
        # スライダー操作中は無視
        if hasattr(self, "scale") and self._is_sliding:
            return

        try:
            new_value = self.knob_value.spec.type_(self.var.get())
            self.knob_value.value = new_value

            # スライダーがある場合は値を同期
            if hasattr(self, "scale_var"):
                self.scale_var.set(float(new_value))

            # デバウンス処理
            if self._entry_timer:
                self.frame.after_cancel(self._entry_timer)

            self._entry_timer = self.frame.after(
                300,  # 300ms delay
                lambda: self.on_change(new_value),
            )
        except (ValueError, TypeError):
            pass

    def _on_scale_press(self, event):
        """スライダーのマウスダウン時"""
        self._is_sliding = True

    def _on_scale_release(self, event):
        """スライダーのマウスリリース時"""
        self._is_sliding = False
        # 保留中の値があれば更新を実行
        if self._pending_value is not None:
            self.on_change(self._pending_value)
            self._pending_value = None

    def _on_scale_change(self, *args):
        """スライダー変更時"""
        new_value = self.knob_value.spec.type_(self.scale_var.get())
        self.var.set(str(new_value))
        self.knob_value.value = new_value

        if self._is_sliding:
            # スライダー操作中は値を保留
            self._pending_value = new_value
        else:
            # プログラムによる変更（初期化など）は即座に反映
            self.on_change(new_value)


class BooleanKnobControl(KnobControlBase):
    """ブール値チェックボックス"""

    def __init__(self, parent, knob_value, on_change):
        super().__init__(parent, knob_value, on_change)

    def _setup_ui(self):
        spec = self.knob_value.spec

        # チェックボックス
        self.var = tk.BooleanVar(value=self.knob_value.value)
        checkbox = ttk.Checkbutton(self.frame, text=spec.name, variable=self.var)
        checkbox.pack(side="left", anchor="w")
        # チェックボックスは即座に反映（デバウンス不要）
        self.var.trace_add("write", self._on_change_callback)

    def _on_change_callback(self, *args):
        """チェックボックス変更時"""
        new_value = self.var.get()
        self.knob_value.value = new_value
        self.on_change(new_value)


class SelectKnobControl(KnobControlBase):
    """選択肢ドロップダウン"""

    def __init__(self, parent, knob_value, on_change):
        super().__init__(parent, knob_value, on_change)

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
        # ドロップダウンは即座に反映
        self.var.trace_add("write", self._on_change_callback)

    def _on_change_callback(self, *args):
        """ドロップダウン変更時"""
        new_value = self.var.get()
        self.knob_value.value = new_value
        self.on_change(new_value)


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
