# storybook/app.py - StorybookApplication
"""TkApplicationやThemedApplicationのようなStorybookApplication。"""

from pubsubtk import ThemedApplication, TkApplication

from .container import StorybookContainer
from .state import StorybookState


class StorybookApplication(TkApplication[StorybookState]):
    """Storybook専用のアプリケーションクラス"""

    def __init__(
        self,
        title: str = "PubSubTk Storybook",
        geometry: str = "1200x800",
        auto_setup: bool = True,
        *args,
        **kwargs,
    ):
        """Storybookアプリケーションを初期化する。

        Args:
            title: ウィンドウタイトル
            geometry: ウィンドウサイズ
            auto_setup: 自動でStorybookコンテナを配置するか
        """
        super().__init__(
            StorybookState, title=title, geometry=geometry, *args, **kwargs
        )

        if auto_setup:
            self._setup_storybook()

    def _setup_storybook(self):
        """Storybookコンテナを自動配置"""
        sb = StorybookContainer(parent=self.main_frame, store=self.store)
        sb.pack(fill="both", expand=True)


class ThemedStorybookApplication(ThemedApplication[StorybookState]):
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
        """テーマ対応Storybookアプリケーションを初期化する。

        Args:
            theme: ttkテーマ名
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
