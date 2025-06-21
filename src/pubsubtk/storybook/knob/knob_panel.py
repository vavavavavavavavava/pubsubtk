# storybook/knob/knob_panel.py
"""KnobコントロールパネルのメインUI"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List

from pubsubtk import ContainerComponentTtk
from pubsubtk.storybook.state import StorybookState
from .knob_types import KnobValue
from .knob_controls import create_knob_control


class KnobPanel(ContainerComponentTtk[StorybookState]):
    """Knob制御パネル"""
    
    def __init__(self, parent, store):
        super().__init__(parent=parent, store=store)
        self.knob_controls: Dict[str, any] = {}
        self.knob_values: Dict[str, KnobValue] = {}
    
    def setup_ui(self):
        # スクロール可能なフレーム
        self.canvas = tk.Canvas(self, bg="white")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # レイアウト
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 初期メッセージ
        self._show_empty_message()
    
    def setup_subscriptions(self):
        # PreviewFrameからのKnob情報更新を購読
        self.subscribe("storybook.knobs.update", self._on_knobs_update)
    
    def refresh_from_state(self):
        pass
    
    def update_knobs(self, knob_values: Dict[str, KnobValue]):
        """Knobリストを更新"""
        self.knob_values = knob_values
        self._rebuild_knob_ui()
    
    def _rebuild_knob_ui(self):
        """Knob UIを再構築"""
        # 既存のコントロールをクリア
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.knob_controls.clear()
        
        if not self.knob_values:
            self._show_empty_message()
            return
        
        # ヘッダー
        header = ttk.Label(self.scrollable_frame, text="Controls", 
                          font=("", 12, "bold"), padding=(5, 10))
        header.pack(fill="x", padx=10, pady=(5, 10))
        
        # 各Knobのコントロールを作成
        for name, knob_value in self.knob_values.items():
            self._create_knob_row(name, knob_value)
    
    def _create_knob_row(self, name: str, knob_value: KnobValue):
        """個別のKnobコントロール行を作成"""
        # コンテナフレーム
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.pack(fill="x", padx=10, pady=2)
        
        # 説明文（desc指定時）
        if knob_value.spec.desc:
            desc_label = ttk.Label(row_frame, text=knob_value.spec.desc, 
                                  font=("", 8), foreground="gray")
            desc_label.pack(anchor="w", pady=(0, 2))
        
        # コントロール作成
        control = create_knob_control(
            row_frame, 
            knob_value, 
            lambda value, n=name: self._on_knob_change(n, value)
        )
        control.pack(fill="x", pady=(0, 10))
        
        self.knob_controls[name] = control
    
    def _on_knob_change(self, knob_name: str, new_value):
        """Knob値変更時のコールバック"""
        # PreviewFrameに変更を通知してストーリーを再描画
        # 注意: knob UI自体は再構築しない（値が保持される）
        self.publish("storybook.knob.changed", knob_name=knob_name, value=new_value)
    
    def _show_empty_message(self):
        """空状態のメッセージ表示"""
        empty_frame = ttk.Frame(self.scrollable_frame)
        empty_frame.pack(expand=True, fill="both")
        
        message_label = ttk.Label(
            empty_frame, 
            text="No controls available\nSelect a story with knobs", 
            font=("", 10), 
            foreground="gray",
            justify="center"
        )
        message_label.pack(expand=True)
    
    def _on_knobs_update(self, knob_values: Dict[str, KnobValue]):
        """PreviewFrameからのKnob更新メッセージを受信"""
        self.update_knobs(knob_values)