from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from pubsub import pub


class PubSubBase(ABC):
    """
    PubSubパターンの基底クラス。

    - setup_subscriptions()で購読設定を行う抽象メソッドを提供
    - subscribe()/send_message()/unsubscribe()/unsubscribe_all()で購読管理
    - teardown()で全購読解除
    - 継承先で購読設定を簡潔に記述可能
    """

    def __init__(self, *args, **kwargs):
        self._subscriptions: List[Dict[str, Any]] = []
        self.setup_subscriptions()

    def subscribe(self, topic: str, handler: Callable, **kwargs) -> None:
        pub.subscribe(handler, topic, **kwargs)
        self._subscriptions.append({"topic": topic, "handler": handler})

    def send_message(self, topic: str, **kwargs) -> None:
        pub.sendMessage(topic, **kwargs)

    def unsubscribe(self, topic: str, handler: Callable) -> None:
        pub.unsubscribe(handler, topic)
        self._subscriptions = [
            s
            for s in self._subscriptions
            if not (s["topic"] == topic and s["handler"] == handler)
        ]

    def unsubscribe_all(self) -> None:
        for s in list(self._subscriptions):
            pub.unsubscribe(s["handler"], s["topic"])
        self._subscriptions.clear()

    @abstractmethod
    def setup_subscriptions(self) -> None:
        """
        継承先で購読設定を行うためのメソッド。

        例:
            class MyPS(PubSubBase):
                def setup_subscriptions(self):
                    self.subscribe(TopicEnum.STATE_CHANGED, self.on_change)
        """
        pass

    def teardown(self) -> None:
        """
        全ての購読を解除する。
        """
        self.unsubscribe_all()
