# storybook/container.py - StorybookContainer
"""Storybook を構成する最上位 Container。"""

from pubsubtk import ContainerComponentTtk
from pubsubtk.storybook.processor import StorybookProcessor
from pubsubtk.storybook.state import StorybookState
from pubsubtk.storybook.template import StorybookTemplate
from pubsubtk.storybook.views.preview import PreviewFrame
from pubsubtk.storybook.views.sidebar import SidebarView


class StorybookContainer(ContainerComponentTtk[StorybookState]):
    """Storybook 全体を管理するコンテナ（テーマ対応）"""

    def setup_ui(self):
        # テンプレートを直接インスタンス化して配置
        self.template = StorybookTemplate(parent=self, store=self.store)
        self.template.pack(fill="both", expand=True)

        # 子ビューをスロットに差し込む（テンプレート経由）
        self.template.switch_slot_content("sidebar", SidebarView)
        self.template.switch_slot_content("preview", PreviewFrame)

        # Processor 登録
        self.pub_register_processor(StorybookProcessor, "storybook")

    def setup_subscriptions(self):
        pass

    def refresh_from_state(self):
        # 今回は個別 Slots が自前でリフレッシュするため何もしない
        pass
