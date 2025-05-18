from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, Type

from pubsubtk.core.pubsub_base import PubSubBase
from pubsubtk.topic.topics import (
    DefaultNavigateTopic,
    DefaultProcessorTopic,
    DefaultUpdateTopic,
)

if TYPE_CHECKING:
    # 型チェック時（mypy や IDE 補完時）のみ読み込む
    from pubsubtk.processor.processor_base import ProcessorBase
    from pubsubtk.ui.base.container_base import ContainerComponentType


class PubSubDefaultTopicBase(PubSubBase):
    def pub_switch_container(
        self,
        cls: ContainerComponentType,
        **kwargs: Any,
    ) -> None:
        """コンテナを切り替えるPubSubメッセージを送信する。

        Args:
            cls (ContainerComponentType): 切り替え先のコンテナコンポーネントクラス
            **kwargs (Any): コンテナに渡すキーワード引数

        Note:
            コンテナは、TkApplicationまたはTtkApplicationのコンストラクタで指定された
            親ウィジェットの子として配置されます。
        """
        self.publish(DefaultNavigateTopic.SWITCH_CONTAINER, cls=cls, **kwargs)

    def pub_open_subwindow(
        self,
        cls: ContainerComponentType,
        win_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """サブウィンドウを開くPubSubメッセージを送信する。

        Args:
            cls (ContainerComponentType): サブウィンドウに表示するコンテナコンポーネントクラス
            win_id (Optional[str], optional): サブウィンドウのID。
                指定しない場合は自動生成される。
                同じIDを指定すると、既存のウィンドウが再利用される。
            **kwargs (Any): コンテナに渡すキーワード引数

        Note:
            サブウィンドウは、Toplevel ウィジェットとして作成されます。
        """
        self.publish(
            DefaultNavigateTopic.OPEN_SUBWINDOW, cls=cls, win_id=win_id, **kwargs
        )

    def pub_close_subwindow(self, win_id: str) -> None:
        """サブウィンドウを閉じるPubSubメッセージを送信する。

        Args:
            win_id (str): 閉じるサブウィンドウのID
        """
        self.publish(DefaultNavigateTopic.CLOSE_SUBWINDOW, win_id=win_id)

    def pub_close_all_subwindows(self) -> None:
        """すべてのサブウィンドウを閉じるPubSubメッセージを送信する。"""
        self.publish(DefaultNavigateTopic.CLOSE_ALL_SUBWINDOWS)

    def pub_update_state(self, state_path: str, new_value: Any) -> None:
        """Storeの状態を更新するPubSubメッセージを送信する。

        Args:
            state_path (str): 更新する状態のパス（例: "user.name", "items[2].value"）
            new_value (Any): 新しい値

        Note:
            状態パスは、Store.state プロキシを使用して取得することを推奨します。
            例: `store.update_state(store.state.user.name, "新しい名前")`
        """
        self.publish(
            DefaultUpdateTopic.UPDATE_STATE,
            state_path=str(state_path),
            new_value=new_value,
        )

    def pub_add_to_list(self, state_path: str, item: Any) -> None:
        """Storeの状態（リスト）に要素を追加するPubSubメッセージを送信する。

        Args:
            state_path (str): 要素を追加するリストの状態パス（例: "items", "user.tasks"）
            item (Any): 追加する要素

        Note:
            状態パスは、Store.state プロキシを使用して取得することを推奨します。
            例: `store.add_to_list(store.state.items, new_item)`
        """
        self.publish(
            DefaultUpdateTopic.ADD_TO_LIST, state_path=str(state_path), item=item
        )

    def pub_registor_processor(
        self,
        proc: Type[ProcessorBase],
        name: Optional[str] = None,
    ) -> None:
        """Processorを登録するPubSubメッセージを送信する。

        Args:
            proc (Type[ProcessorBase]): 登録するProcessorクラス
            name (Optional[str], optional): Processorの名前。
                省略した場合はクラス名が使用される。Defaults to None.

        Note:
            登録されたProcessorは、アプリケーションのライフサイクルを通じて有効です。
        """
        self.publish(DefaultProcessorTopic.REGISTOR_PROCESSOR, proc=proc, name=name)

    def pub_delete_processor(self, name: str) -> None:
        """指定した名前のProcessorを削除するPubSubメッセージを送信する。

        Args:
            name (str): 削除するProcessorの名前
        """
        self.publish(DefaultProcessorTopic.DELETE_PROCESSOR, name=name)

    def sub_state_changed(
        self, state_path: str, handler: Callable[[Any, Any], None]
    ) -> None:
        """状態が変更されたときの通知を購読する。

        ハンドラー関数には、old_valueとnew_valueが渡されます。

        Args:
            state_path (str): 監視する状態のパス（例: "user.name", "items[2].value"）
            handler (Callable[[Any, Any], None]): 変更時に呼び出される関数。
                old_valueとnew_valueの2引数を取る
        """
        self.subscribe(f"{DefaultUpdateTopic.STATE_CHANGED}.{str(state_path)}", handler)

    def sub_state_added(
        self, state_path: str, handler: Callable[[Any, int], None]
    ) -> None:
        """リストに要素が追加されたときの通知を購読する。

        ハンドラー関数には、itemとindexが渡されます。

        Args:
            state_path (str): 監視するリスト状態のパス（例: "items", "user.tasks"）
            handler (Callable[[Any, int], None]): 要素追加時に呼び出される関数。
                追加されたアイテムとそのインデックスを引数に取る
        """
        self.subscribe(f"{DefaultUpdateTopic.STATE_ADDED}.{str(state_path)}", handler)
