# default_topic_base.py - デフォルトトピック操作をまとめた基底クラス

"""
src/pubsubtk/core/default_topic_base.py

主要な PubSub トピックに対する便利メソッドを提供します。
"""

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
    from pubsubtk.ui.types import ComponentType, ContainerComponentType


class PubSubDefaultTopicBase(PubSubBase):
    """
    Built-in convenience methods for common PubSub operations.

    **IMPORTANT**: Container and Processor components should use these built-in methods
    instead of manually publishing to DefaultTopics. These methods are designed for
    ease of use and provide better IDE support.
    """

    def pub_switch_container(
        self,
        cls: ContainerComponentType,
        kwargs: dict = None,
    ) -> None:
        """コンテナを切り替えるPubSubメッセージを送信する。

        Args:
            cls (ContainerComponentType): 切り替え先のコンテナコンポーネントクラス
            kwargs: コンテナに渡すキーワード引数用辞書

        Note:
            コンテナは、TkApplicationまたはTtkApplicationのコンストラクタで指定された
            親ウィジェットの子として配置されます。
        """
        self.publish(DefaultNavigateTopic.SWITCH_CONTAINER, cls=cls, kwargs=kwargs)

    def pub_switch_slot(
        self,
        slot_name: str,
        cls: ComponentType,
        kwargs: dict = None,
    ) -> None:
        """テンプレートの特定スロットのコンテンツを切り替える。

        Args:
            slot_name (str): スロット名
            cls (ComponentType): コンテナまたはプレゼンテーショナルコンポーネントクラス
            kwargs: コンポーネントに渡すキーワード引数用辞書

        Note:
            ContainerComponentとPresentationalComponentの両方に対応。
            テンプレートが設定されていない場合はエラーになります。
        """
        self.publish(
            DefaultNavigateTopic.SWITCH_SLOT,
            slot_name=slot_name,
            cls=cls,
            kwargs=kwargs,
        )

    def pub_open_subwindow(
        self,
        cls: ComponentType,
        win_id: Optional[str] = None,
        kwargs: dict = None,
    ) -> None:
        """サブウィンドウを開くPubSubメッセージを送信する。

        Args:
            cls (ComponentType): サブウィンドウに表示するコンポーネントクラス
            win_id (Optional[str], optional): サブウィンドウのID。
                指定しない場合は自動生成される。
                同じIDを指定すると、既存のウィンドウが再利用される。
            kwargs: コンポーネントに渡すキーワード引数用辞書

        Note:
            サブウィンドウは、Toplevel ウィジェットとして作成されます。
        """
        self.publish(
            DefaultNavigateTopic.OPEN_SUBWINDOW, cls=cls, win_id=win_id, kwargs=kwargs
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
        """
        Storeの状態を更新するPubSubメッセージを送信する。

        Args:
            state_path (str): 更新する状態のパス（例: "user.name", "items[2].value"）
            new_value (Any): 新しい値

        Note:
            **RECOMMENDED**: Use store.state proxy for type-safe paths with IDE support:
            `self.pub_update_state(str(self.store.state.user.name), "新しい名前")`
            The state proxy provides autocomplete and "Go to Definition" functionality.
        """
        self.publish(
            DefaultUpdateTopic.UPDATE_STATE,
            state_path=str(state_path),
            new_value=new_value,
        )

    def pub_add_to_list(self, state_path: str, item: Any) -> None:
        """
        Storeの状態（リスト）に要素を追加するPubSubメッセージを送信する。

        Args:
            state_path (str): 要素を追加するリストの状態パス（例: "items", "user.tasks"）
            item (Any): 追加する要素

        Note:
            **RECOMMENDED**: Use store.state proxy for type-safe paths with IDE support:
            `self.pub_add_to_list(str(self.store.state.items), new_item)`
            The state proxy provides autocomplete and "Go to Definition" functionality.
        """
        self.publish(
            DefaultUpdateTopic.ADD_TO_LIST, state_path=str(state_path), item=item
        )

    def pub_add_to_dict(self, state_path: str, key: str, value: Any) -> None:
        """Storeの状態(辞書)に要素を追加するPubSubメッセージを送信する。

        Args:
            state_path: 要素を追加する辞書の状態パス。
            key: 追加するキー。
            value: 追加する値。

        Note:
            **RECOMMENDED**: Use store.state proxy for type-safe paths with IDE support:
            `self.pub_add_to_dict(str(self.store.state.mapping), "k", v)`
        """
        self.publish(
            DefaultUpdateTopic.ADD_TO_DICT,
            state_path=str(state_path),
            key=key,
            value=value,
        )

    def pub_register_processor(
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
        self.publish(DefaultProcessorTopic.REGISTER_PROCESSOR, proc=proc, name=name)

    def pub_delete_processor(self, name: str) -> None:
        """指定した名前のProcessorを削除するPubSubメッセージを送信する。

        Args:
            name (str): 削除するProcessorの名前
        """
        self.publish(DefaultProcessorTopic.DELETE_PROCESSOR, name=name)

    def sub_state_changed(
        self, state_path: str, handler: Callable[[Any, Any], None]
    ) -> None:
        """
        状態が変更されたときの詳細通知を購読する。

        ハンドラー関数には、old_valueとnew_valueが渡されます。

        Args:
            state_path (str): 監視する状態のパス（例: "user.name", "items[2].value"）
            handler (Callable[[Any, Any], None]): 変更時に呼び出される関数。
                old_valueとnew_valueの2引数を取る

        Note:
            **RECOMMENDED**: Use store.state proxy for consistent path specification:
            `self.sub_state_changed(str(self.store.state.user.name), self.on_name_changed)`
        """
        self.subscribe(f"{DefaultUpdateTopic.STATE_CHANGED}.{str(state_path)}", handler)

    def sub_for_refresh(
        self, state_path: str, handler: Callable[[], None]
    ) -> None:
        """
        状態が更新されたときにUI再描画用のシンプルな通知を購読する。

        ハンドラー関数は引数なしで呼び出され、ハンドラー内で必要に応じて
        store.get_current_state()を使用して現在の状態を取得できます。

        Args:
            state_path (str): 監視する状態のパス（例: "user.name", "items[2].value"）
            handler (Callable[[], None]): 更新時に呼び出される引数なしの関数

        Note:
            **RECOMMENDED**: Use store.state proxy for consistent path specification:
            `self.sub_for_refresh(str(self.store.state.user.name), self.refresh_ui)`
            
            このメソッドは、変更内容に関係なく「状態が変わったからUI更新」という
            パターンに最適です。refresh_from_state()と同じロジックを使い回せます。
        """
        self.subscribe(f"{DefaultUpdateTopic.STATE_UPDATED}.{str(state_path)}", handler)

    def sub_state_added(
        self, state_path: str, handler: Callable[[Any, int], None]
    ) -> None:
        """
        リストに要素が追加されたときの通知を購読する。

        ハンドラー関数には、itemとindexが渡されます。

        Args:
            state_path (str): 監視するリスト状態のパス（例: "items", "user.tasks"）
            handler (Callable[[Any, int], None]): 要素追加時に呼び出される関数。
                追加されたアイテムとそのインデックスを引数に取る

        Note:
            **RECOMMENDED**: Use store.state proxy for consistent path specification:
            `self.sub_state_added(str(self.store.state.items), self.on_item_added)`
        """
        self.subscribe(f"{DefaultUpdateTopic.STATE_ADDED}.{str(state_path)}", handler)

    def sub_dict_item_added(
        self, state_path: str, handler: Callable[[str, Any], None]
    ) -> None:
        """辞書に要素が追加されたときの通知を購読する。

        ハンドラー関数には、キーと値が渡されます。

        Args:
            state_path: 監視する辞書状態のパス。
            handler: 追加されたキーと値を引数に取る関数。

        Note:
            **RECOMMENDED**: Use store.state proxy for consistent path specification:
            `self.sub_dict_item_added(str(self.store.state.mapping), self.on_added)`
        """
        self.subscribe(
            f"{DefaultUpdateTopic.DICT_ADDED}.{str(state_path)}",
            handler,
        )