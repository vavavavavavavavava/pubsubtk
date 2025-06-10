"""
tests/sample_app/main.py

簡易デモアプリケーション
"""

import asyncio
import tkinter as tk
from enum import auto
from tkinter import messagebox

from pydantic import BaseModel

from pubsubtk import (
    AutoNamedTopic,
    ContainerComponentTk,
    PresentationalComponentTk,
    ProcessorBase,
    TemplateComponentTk,
    TkApplication,
    make_async_task,
)


# カスタムトピック定義
class AppTopic(AutoNamedTopic):
    INCREMENT = auto()  # -> "AppTopic.increment"
    RESET = auto()  # -> "AppTopic.reset"
    MILESTONE = auto()  # -> "AppTopic.milestone"


class AppState(BaseModel):
    counter: int = 0
    total_clicks: int = 0


# テンプレート定義
class AppTemplate(TemplateComponentTk[AppState]):
    def define_slots(self):
        # ヘッダー
        self.header = tk.Frame(self, height=50, bg="lightblue")
        self.header.pack(fill=tk.X)

        # メインコンテンツ
        self.main = tk.Frame(self)
        self.main.pack(fill=tk.BOTH, expand=True)

        return {
            "header": self.header,
            "main": self.main,
        }


# Presentationalコンポーネント（ヘッダー表示）
class HeaderView(PresentationalComponentTk):
    def setup_ui(self):
        self.label = tk.Label(
            self, text="PubSubTk Demo", font=("Arial", 16), bg="lightblue"
        )
        self.label.pack(pady=10)

    def update_data(self, total_clicks: int):
        self.label.config(text=f"PubSubTk Demo - Total Clicks: {total_clicks}")


# Containerコンポーネント（ヘッダー管理） - sub_for_refreshを使用
class HeaderContainer(ContainerComponentTk[AppState]):
    def setup_ui(self):
        self.header_view = HeaderView(self)
        self.header_view.pack(fill=tk.BOTH, expand=True)

    def setup_subscriptions(self):
        # 新しいsub_for_refreshを使用 - 引数なしでシンプル
        self.sub_for_refresh(str(self.store.state.total_clicks), self.refresh_header)

    def refresh_from_state(self):
        self.refresh_header()

    def refresh_header(self):
        """引数なしのハンドラー - 必要に応じてstore.get_current_state()で現在値を取得"""
        state = self.store.get_current_state()
        self.header_view.update_data(state.total_clicks)


# Containerコンポーネント（メインカウンター） - 従来のsub_state_changedも併用
class CounterContainer(ContainerComponentTk[AppState]):
    """カウンター表示とアイテム削除を管理するコンテナ。"""

    def setup_ui(self):
        # カウンター表示
        self.counter_label = tk.Label(self, text="0", font=("Arial", 32))
        self.counter_label.pack(pady=30)

        # アイテムリスト
        self.item_list = tk.Listbox(self, height=5)
        for i in range(5):
            self.item_list.insert(tk.END, f"Item {i + 1}")
        self.item_list.pack(pady=10)

        # ボタン
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame, text="カウントアップ", command=self.increment, font=("Arial", 12)
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame, text="リセット", command=self.reset, font=("Arial", 12)
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame, text="削除", command=self.delete_selected, font=("Arial", 12)
        ).pack(side=tk.LEFT, padx=10)

    def setup_subscriptions(self):
        # 2つの方法を比較
        # 1. 従来の方法（old_value, new_valueを受け取るが使わない）
        self.sub_state_changed(
            str(self.store.state.counter), self.on_counter_changed_old_way
        )

        # 2. 新しい方法（引数なしでシンプル）
        # self.sub_for_refresh(str(self.store.state.counter), self.on_counter_refresh_new_way)

        self.subscribe(AppTopic.MILESTONE, self.on_milestone)

    def refresh_from_state(self):
        state = self.store.get_current_state()
        self.counter_label.config(text=str(state.counter))

    def increment(self):
        # カスタムトピックでインクリメント通知
        self.publish(AppTopic.INCREMENT)

    def reset(self):
        # カスタムトピックでリセット通知
        self.publish(AppTopic.RESET)

    def delete_selected(self) -> None:
        """選択アイテムの削除処理を開始する。"""
        self.confirm_delete()

    @make_async_task
    async def confirm_delete(self) -> None:
        """削除確認後にリストからアイテムを除去する。"""

        await asyncio.sleep(0)
        selection = self.item_list.curselection()
        if not selection:
            return
        if messagebox.askyesno("確認", "選択項目を削除しますか？"):
            self.item_list.delete(selection[0])

    def on_counter_changed_old_way(self, old_value, new_value):
        """従来の方法 - old_value, new_valueを受け取るが実際は new_value しか使わない"""
        self.counter_label.config(text=str(new_value))

    def on_counter_refresh_new_way(self):
        """新しい方法 - 引数なしでシンプル、必要に応じてstoreから現在値を取得"""
        state = self.store.get_current_state()
        self.counter_label.config(text=str(state.counter))

    def on_milestone(self, value: int):
        messagebox.showinfo("マイルストーン!", f"{value} に到達しました！")


# Processor（ビジネスロジック）
class CounterProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe(AppTopic.INCREMENT, self.handle_increment)
        self.subscribe(AppTopic.RESET, self.handle_reset)

    def handle_increment(self):
        state = self.store.get_current_state()
        new_counter = state.counter + 1
    app.run(use_async=True)

        # StateProxyで型安全な状態更新
        self.pub_update_state(str(self.store.state.counter), new_counter)
        self.pub_update_state(str(self.store.state.total_clicks), new_total)

        # マイルストーン判定
        if new_counter % 10 == 0:
            self.publish(AppTopic.MILESTONE, value=new_counter)

    def handle_reset(self):
        # 便利メソッドで状態リセット
        self.pub_update_state(str(self.store.state.counter), 0)


if __name__ == "__main__":
    app = TkApplication(AppState, title="PubSubTk Simple Demo", geometry="400x300")
    # Processor登録
    app.pub_register_processor(CounterProcessor)

    # テンプレート設定
    app.set_template(AppTemplate)

    # 各スロットにコンポーネント配置
    app.pub_switch_slot("header", HeaderContainer)
    app.pub_switch_slot("main", CounterContainer)

    # 起動
    app.run(use_async=True)
