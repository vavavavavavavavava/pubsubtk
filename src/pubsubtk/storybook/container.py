# storybook/container.py - StorybookContainer
"""Storybook を構成する最上位 Container。"""

from pubsubtk import ContainerComponentTk

from .processor import StorybookProcessor
from .state import StorybookState
from .template import StorybookTemplate
from .views.knobs import KnobPanel
from .views.preview import PreviewFrame
from .views.sidebar import SidebarView


class StorybookContainer(ContainerComponentTk[StorybookState]):
    """Storybook 全体を管理するコンテナ"""

    def setup_ui(self):
        # テンプレートを直接インスタンス化して配置
        self.template = StorybookTemplate(parent=self, store=self.store)
        self.template.pack(fill="both", expand=True)

        # 子ビューをスロットに差し込む（テンプレート経由）
        self.template.switch_slot_content("sidebar", SidebarView)
        self.template.switch_slot_content("preview", PreviewFrame)
        self.template.switch_slot_content("knobs", KnobPanel)

        # Processor 登録
        self.pub_register_processor(StorybookProcessor, "storybook")

        # SidebarViewにPubSub発行機能を追加
        sidebar_widget = self.template.get_slot_content("sidebar")
        if sidebar_widget and hasattr(sidebar_widget, "set_publish_callback"):
            sidebar_widget.set_publish_callback(self.publish)

    def refresh_from_state(self):
        # 今回は個別 Slots が自前でリフレッシュするため何もしない
        pass
