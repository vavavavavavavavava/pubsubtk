# storybook/app.py - StorybookApplication
"""ThemedApplicationベースのStorybookApplication。"""

from pubsubtk import ThemedApplication

from .core.state import StorybookState
from .ui.container import StorybookContainer


class StorybookApplication(ThemedApplication[StorybookState]):
    """テーマ対応Storybook専用のアプリケーションクラス"""

    def __init__(
        self,
        theme: str = "arc",
        title: str = "PubSubTk Storybook",
        geometry: str = "1200x800",
        auto_setup: bool = True,
        *args,
        **kwargs,
    ):
        """Storybookアプリケーションを初期化する。

        Args:
            theme: ttkテーマ名（arc, clam, alt, default, classic等）
            title: ウィンドウタイトル
            geometry: ウィンドウサイズ
            auto_setup: 自動でStorybookコンテナを配置するか
        """
        super().__init__(
            StorybookState, theme=theme, title=title, geometry=geometry, *args, **kwargs
        )

        if auto_setup:
            self._setup_storybook()

    def _setup_storybook(self):
        """Storybookコンテナを自動配置"""
        sb = StorybookContainer(parent=self.main_frame, store=self.store)
        sb.pack(fill="both", expand=True)
