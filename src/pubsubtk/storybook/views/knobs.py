# storybook/views/knobs.py - KnobPanel
"""右下の Knob 編集パネル。"""

import tkinter as tk
from tkinter import ttk
from typing import Any, List

from pubsubtk import ContainerComponentTk

from ..meta import KnobSpec
from ..state import StorybookState
from ..topic import SBTopic


class KnobPanel(ContainerComponentTk[StorybookState]):
    """動的プロパティを編集する UI"""

    def setup_ui(self):
        self.inner = tk.Frame(self)
        self.inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def setup_subscriptions(self):
        self.sub_for_refresh(str(self.store.state.active_story_id), self.clear_panel)
        self.subscribe(SBTopic.KNOB_CHANGED, self._update_knobs)

    def refresh_from_state(self):
        self.clear_panel()

    def clear_panel(self):
        for w in self.inner.winfo_children():
            w.destroy()

    def _update_knobs(self, name: str, value: Any):
        if name != "__init__":
            return  # ここでは初回 only

        knob_specs: List[KnobSpec] = value
        self.clear_panel()
        for spec in knob_specs:
            self._create_editor(spec)

    def _create_editor(self, spec: KnobSpec):
        lbl = tk.Label(self.inner, text=spec.name)
        lbl.pack(anchor="w")

        if spec.choices:
            cb = ttk.Combobox(
                self.inner, textvariable=spec.var, values=spec.choices, width=18
            )
            cb.pack(fill="x", pady=2)
            cb.bind("<<ComboboxSelected>>", self._on_change(spec))
        elif spec.type_ is bool:
            chk = ttk.Checkbutton(self.inner, variable=spec.var, text=spec.desc)
            chk.pack(anchor="w", pady=2)
            chk.configure(command=self._callback(spec))
        elif spec.type_ in (int, float) and spec.range:
            lo, hi, st = spec.range
            sp = ttk.Spinbox(
                self.inner,
                from_=lo,
                to=hi,
                increment=st,
                textvariable=spec.var,
                width=10,
            )
            sp.pack(anchor="w", pady=2)
            sp.bind("<Return>", self._on_change(spec))
        elif spec.type_ in (int, float):
            ent = ttk.Entry(self.inner, textvariable=spec.var, width=10)
            ent.pack(anchor="w", pady=2)
            ent.bind("<Return>", self._on_change(spec))
        elif spec.multiline:
            txt = tk.Text(self.inner, height=3, width=25)
            txt.insert("1.0", spec.var.get())
            txt.bind(
                "<<Modified>>",
                lambda e, s=spec, t=txt: (
                    spec.var.set(t.get("1.0", "end-1c")),
                    t.edit_modified(0),
                    self._publish_knob(s),
                ),
            )
            txt.pack(fill="x", pady=2)
        else:
            ent = ttk.Entry(self.inner, textvariable=spec.var)
            ent.pack(fill="x", pady=2)
            ent.bind("<Return>", self._on_change(spec))

    def _callback(self, spec):
        return lambda: self._publish_knob(spec)

    def _on_change(self, spec):
        return lambda *_: self._publish_knob(spec)

    def _publish_knob(self, spec):
        self.publish(SBTopic.KNOB_CHANGED, name=spec.name, value=spec.var.get())
