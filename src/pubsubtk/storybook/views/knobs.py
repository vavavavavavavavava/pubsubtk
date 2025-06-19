# storybook/views/knobs.py - KnobPanel
"""右下の Knob 編集パネル。"""

import tkinter as tk
from tkinter import ttk
from typing import Any, List

from pubsubtk import ContainerComponentTtk
from pubsubtk.storybook.meta import KnobControl, KnobSpec
from pubsubtk.storybook.state import StorybookState
from pubsubtk.storybook.topic import SBTopic


class KnobPanel(ContainerComponentTtk[StorybookState]):
    """動的プロパティを編集する UI（テーマ対応）"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.knob_controls: List[KnobControl] = []

    def setup_ui(self):
        # スクロール可能なキャンバス
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # レイアウト
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 初期メッセージ
        self._show_empty_state()

        # マウスホイールバインド
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def setup_subscriptions(self):
        self.sub_for_refresh(str(self.store.state.active_story_id), self.clear_panel)
        self.subscribe(SBTopic.KNOB_CHANGED, self._update_knobs)

    def refresh_from_state(self):
        self.clear_panel()

    def _on_mousewheel(self, event):
        """マウスホイールでスクロール"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear_panel(self):
        """パネルをクリア"""
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
        self._show_empty_state()

    def _show_empty_state(self):
        """空の状態を表示"""
        empty_frame = ttk.Frame(self.scrollable_frame)
        empty_frame.pack(expand=True, fill="both", padx=20, pady=20)

        ttk.Label(empty_frame, text="🎛️", font=("", 32)).pack(pady=(20, 5))

        ttk.Label(
            empty_frame, text="No controls available", font=("", 10), foreground="gray"
        ).pack()

    def _update_knobs(self, name: str, value: Any):
        if name != "__init__":
            return  # ここでは初回 only

        knob_specs: List[KnobSpec] = value
        self.clear_panel()

        if not knob_specs:
            self._show_empty_state()
            return

        # KnobControlオブジェクトを作成
        self.knob_controls = []
        for spec in knob_specs:
            var = self._create_tkinter_var(spec)
            control = KnobControl(spec=spec, var=var)
            self.knob_controls.append(control)

        # ヘッダー
        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(header_frame, text="Controls", font=("", 11, "bold")).pack(
            side="left"
        )
        ttk.Label(
            header_frame,
            text=f"({len(self.knob_controls)} items)",
            font=("", 9),
            foreground="gray",
        ).pack(side="left", padx=(5, 0))

        # コントロール群
        for i, control in enumerate(self.knob_controls):
            self._create_editor(control, i == len(self.knob_controls) - 1)

    def _create_tkinter_var(self, spec: KnobSpec) -> tk.Variable:
        """KnobSpecから適切なtkinter.Variableを作成"""
        if spec.type_ is bool:
            var = tk.BooleanVar(value=spec.default)
        elif spec.type_ is int:
            var = tk.IntVar(value=spec.default)
        elif spec.type_ is float:
            var = tk.DoubleVar(value=spec.default)
        else:
            var = tk.StringVar(value=str(spec.default))
        return var

    def _create_editor(self, control: KnobControl, is_last: bool = False):
        """個別のコントロールエディタを作成"""
        spec = control.spec
        var = control.var

        # メインフレーム
        main_frame = ttk.Frame(self.scrollable_frame)
        main_frame.pack(fill="x", padx=10, pady=5)

        # ラベルフレーム
        label_frame = ttk.Frame(main_frame)
        label_frame.pack(fill="x", pady=(0, 5))

        name_label = ttk.Label(label_frame, text=spec.name, font=("", 10, "bold"))
        name_label.pack(side="left")

        if spec.desc:
            desc_label = ttk.Label(
                label_frame, text=f"• {spec.desc}", font=("", 9), foreground="gray"
            )
            desc_label.pack(side="left", padx=(10, 0))

        # コントロール作成
        if spec.choices:
            cb = ttk.Combobox(
                main_frame, textvariable=var, values=spec.choices, state="readonly"
            )
            cb.pack(fill="x")
            cb.bind("<<ComboboxSelected>>", self._on_change(control))

        elif spec.type_ is bool:
            chk = ttk.Checkbutton(main_frame, variable=var, text="Enabled")
            chk.pack(anchor="w")
            chk.configure(command=self._callback(control))

        elif spec.type_ in (int, float) and spec.range:
            # スライダー付きスピンボックス
            control_frame = ttk.Frame(main_frame)
            control_frame.pack(fill="x")

            lo, hi, st = spec.range

            # スライダー
            scale = ttk.Scale(
                control_frame, from_=lo, to=hi, variable=var, orient="horizontal"
            )
            scale.pack(side="left", fill="x", expand=True, padx=(0, 5))

            # スピンボックス
            sp = ttk.Spinbox(
                control_frame,
                from_=lo,
                to=hi,
                increment=st,
                textvariable=var,
                width=8,
            )
            sp.pack(side="right")

            scale.configure(command=lambda v, c=control: self._publish_knob(c))
            sp.bind("<Return>", self._on_change(control))
            sp.bind("<FocusOut>", self._on_change(control))

        elif spec.type_ in (int, float):
            ent = ttk.Entry(main_frame, textvariable=var)
            ent.pack(fill="x")
            ent.bind("<Return>", self._on_change(control))
            ent.bind("<FocusOut>", self._on_change(control))

        elif spec.multiline:
            text_frame = ttk.Frame(main_frame)
            text_frame.pack(fill="x")

            txt = tk.Text(text_frame, height=4, wrap=tk.WORD, font=("", 9))
            scrollbar_text = ttk.Scrollbar(
                text_frame, orient="vertical", command=txt.yview
            )
            txt.configure(yscrollcommand=scrollbar_text.set)

            txt.pack(side="left", fill="both", expand=True)
            scrollbar_text.pack(side="right", fill="y")

            txt.insert("1.0", str(var.get()))
            txt.bind(
                "<<Modified>>",
                lambda e, c=control, t=txt: (
                    c.var.set(t.get("1.0", "end-1c")) if t.edit_modified() else None,
                    t.edit_modified(0),
                    self._publish_knob(c) if t.edit_modified() else None,
                ),
            )
        else:
            ent = ttk.Entry(main_frame, textvariable=var)
            ent.pack(fill="x")
            ent.bind("<Return>", self._on_change(control))
            ent.bind("<FocusOut>", self._on_change(control))

        # 区切り線（最後以外）
        if not is_last:
            ttk.Separator(self.scrollable_frame, orient="horizontal").pack(
                fill="x", padx=10, pady=5
            )

    def _callback(self, control: KnobControl):
        return lambda: self._publish_knob(control)

    def _on_change(self, control: KnobControl):
        return lambda *_: self._publish_knob(control)

    def _publish_knob(self, control: KnobControl):
        self.publish(
            SBTopic.KNOB_CHANGED, name=control.spec.name, value=control.var.get()
        )
