# PubSubTk Library - AI Reference Guide (Medium)

## Overview
PubSubTk is a Python library that provides a clean, type-safe way to build Tkinter/ttk GUI applications using the Publish-Subscribe pattern with Pydantic state management. It enables reactive UI updates and clean separation of concerns.

## Core Classes

### PubSubBase
```python
class PubSubBase(ABC):
    """
    PubSubパターンの基底クラス。
    
    - setup_subscriptions()で購読設定を行う抽象メソッドを提供
    - subscribe()/publish()/unsubscribe()で購読管理
    - teardown()で全購読解除
    - DEBUGレベルでPubSub操作をログ出力
    """
    
    def __init__(self, *args, **kwargs): ...
    
    def subscribe(self, topic: str, handler: Callable, **kwargs) -> None: ...
    
    def publish(self, topic: str, **kwargs) -> None: ...
    
    def unsubscribe(self, topic: str, handler: Callable) -> None: ...
    
    def unsubscribe_all(self) -> None: ...
    
    @abstractmethod
    def setup_subscriptions(self) -> None:
        """
        継承先で購読設定を行うためのメソッド。
        """
        pass
    
    def teardown(self) -> None:
        """
        全ての購読を解除する。
        """
        ...
```

### PubSubDefaultTopicBase
```python
class PubSubDefaultTopicBase(PubSubBase):
    """
    Built-in convenience methods for common PubSub operations.
    
    **IMPORTANT**: Container and Processor components should use these built-in methods
    instead of manually publishing to DefaultTopics. These methods are designed for
    ease of use and provide better IDE support.
    """
    
    def pub_switch_container(self, cls: ContainerComponentType, kwargs: dict = None) -> None:
        """コンテナを切り替えるPubSubメッセージを送信する。"""
        ...
    
    def pub_open_subwindow(self, cls: ContainerComponentType, win_id: Optional[str] = None, kwargs: dict = None) -> None:
        """サブウィンドウを開くPubSubメッセージを送信する。"""
        ...
    
    def pub_close_subwindow(self, win_id: str) -> None:
        """サブウィンドウを閉じるPubSubメッセージを送信する。"""
        ...
    
    def pub_close_all_subwindows(self) -> None:
        """すべてのサブウィンドウを閉じるPubSubメッセージを送信する。"""
        ...
    
    def pub_update_state(self, state_path: str, new_value: Any) -> None:
        """
        Storeの状態を更新するPubSubメッセージを送信する。
        
        **RECOMMENDED**: Use store.state proxy for type-safe paths with IDE support:
        `self.pub_update_state(str(self.store.state.user.name), "新しい名前")`
        """
        ...
    
    def pub_add_to_list(self, state_path: str, item: Any) -> None:
        """
        Storeの状態（リスト）に要素を追加するPubSubメッセージを送信する。
        
        **RECOMMENDED**: Use store.state proxy for type-safe paths with IDE support:
        `self.pub_add_to_list(str(self.store.state.items), new_item)`
        """
        ...
    
    def pub_registor_processor(self, proc: Type[ProcessorBase], name: Optional[str] = None) -> None:
        """Processorを登録するPubSubメッセージを送信する。"""
        ...
    
    def pub_delete_processor(self, name: str) -> None:
        """指定した名前のProcessorを削除するPubSubメッセージを送信する。"""
        ...
    
    def sub_state_changed(self, state_path: str, handler: Callable[[Any, Any], None]) -> None:
        """
        状態が変更されたときの通知を購読する。
        
        **RECOMMENDED**: Use store.state proxy for consistent path specification:
        `self.sub_state_changed(str(self.store.state.user.name), self.on_name_changed)`
        """
        ...
    
    def sub_state_added(self, state_path: str, handler: Callable[[Any, int], None]) -> None:
        """
        リストに要素が追加されたときの通知を購読する。
        
        **RECOMMENDED**: Use store.state proxy for consistent path specification:
        `self.sub_state_added(str(self.store.state.items), self.on_item_added)`
        """
        ...
```

### Store[TState]
```python
class Store(PubSubBase, Generic[TState]):
    """
    型安全な状態管理を提供するジェネリックなStoreクラス。
    
    **KEY FEATURE**: store.state proxy provides IDE autocomplete and type checking
    for state paths. Always prefer `str(store.state.field)` over string literals.
    """
    
    def __init__(self, initial_state_class: Type[TState]): ...
    
    @property
    def state(self) -> TState:
        """
        状態への動的パスアクセス用プロキシを返す。
        
        **USAGE**: str(self.store.state.user.name) -> "user.name" with IDE support
        """
        ...
    
    def get_current_state(self) -> TState:
        """現在の状態のディープコピーを返す。"""
        ...
    
    def update_state(self, state_path: str, new_value: Any) -> None:
        """指定パスの属性を新しい値で更新し、PubSubで変更通知を送信する。"""
        ...
    
    def add_to_list(self, state_path: str, item: Any) -> None:
        """指定パスのリスト属性に要素を追加し、PubSubで追加通知を送信する。"""
        ...

def get_store(state_cls: Type[TState]) -> Store[TState]:
    """
    Store を取得します。未生成の場合は state_cls で新規に作成し、
    それ以外は既存のインスタンスを返します。
    """
    ...
```

### Application Classes

```python
class TkApplication(ApplicationCommon, tk.Tk):
    """Standard Tkinter application with PubSub integration."""
    
    def __init__(self, state_cls: Type[TState], title: str = "Tk App", geometry: str = "800x600", *args, **kwargs): ...
    
    # Inherits all PubSubDefaultTopicBase methods

class ThemedApplication(ApplicationCommon, ThemedTk):
    """Themed ttk application with PubSub integration."""
    
    def __init__(self, state_cls: Type[TState], theme: str = "arc", title: str = "Themed App", geometry: str = "800x600", *args, **kwargs): ...
    
    # Inherits all PubSubDefaultTopicBase methods
    
    def run(self, use_async: bool = False, loop: Optional[asyncio.AbstractEventLoop] = None, poll_interval: int = 50) -> None:
        """Start the application main loop."""
        ...
```

### UI Components

```python
class ContainerMixin(PubSubDefaultTopicBase, ABC, Generic[TState]):
    """
    PubSub連携用のコンテナコンポーネントMixin。
    
    **IMPORTANT**: Use built-in pub_* methods for state updates instead of 
    manually publishing to topics. This provides better IDE support and consistency.
    """
    
    def __init__(self, store: Store[TState], *args, **kwargs: Any): ...
    
    @abstractmethod
    def setup_ui(self) -> None:
        """ウィジェット構築とレイアウトを行うメソッド。"""
        ...
    
    @abstractmethod
    def refresh_from_state(self) -> None:
        """購読通知または初期化時にUIを状態で更新するメソッド。"""
        ...

class ContainerComponentTk(ContainerMixin[TState], tk.Frame, Generic[TState]):
    """標準tk.FrameベースのPubSub連携コンテナ。"""
    
    def __init__(self, parent: tk.Widget, store: Store[TState], *args, **kwargs: Any): ...
    
    # Inherits all PubSubDefaultTopicBase methods

class ContainerComponentTtk(ContainerMixin[TState], ttk.Frame, Generic[TState]):
    """テーマ対応ttk.FrameベースのPubSub連携コンテナ。"""
    
    def __init__(self, parent: tk.Widget, store: Store[TState], *args, **kwargs: Any): ...
    
    # Inherits all PubSubDefaultTopicBase methods

class PresentationalComponentTk(PresentationalMixin, tk.Frame):
    """標準tk.Frameベースの表示専用コンポーネント。"""
    
    def __init__(self, parent: tk.Widget, *args, **kwargs): ...
    
    @abstractmethod
    def setup_ui(self) -> None:
        """ウィジェット構築とレイアウトを行うメソッド。"""
        ...
    
    @abstractmethod
    def update_data(self, *args: Any, **kwargs: Any) -> None:
        """外部データでUIを更新するためのメソッド。"""
        ...
    
    def register_handler(self, event_name: str, handler: Callable[..., Any]) -> None: ...
    
    def trigger_event(self, event_name: str, **kwargs: Any) -> None: ...

class PresentationalComponentTtk(PresentationalMixin, ttk.Frame):
    """テーマ対応ttk.Frameベースの表示専用コンポーネント。"""
    
    def __init__(self, parent: tk.Widget, *args, **kwargs): ...
    
    # Same abstract methods as PresentationalComponentTk
```

### Processor

```python
class ProcessorBase(PubSubDefaultTopicBase, Generic[TState]):
    """
    Business logic handlers with Store access and PubSub integration.
    
    **IMPORTANT**: Use built-in pub_* and sub_* methods for state operations
    instead of manually working with topics. This ensures consistency and
    provides better IDE support.
    """
    
    def __init__(self, store: Store[TState], *args, **kwargs): ...
    
    # Inherits all PubSubDefaultTopicBase methods
```

## Topic System

```python
class AutoNamedTopic(StrEnum):
    """
    Enumメンバー名を自動で小文字化し、クラス名のプレフィックス付き文字列を値とする列挙型。
    
    Usage:
        class MyTopics(AutoNamedTopic):
            USER_LOGIN = auto()  # -> "MyTopics.user_login"
    """
    
    def _generate_next_value_(name, start, count, last_values): ...
    def __new__(cls, value): ...

class DefaultNavigateTopic(AutoNamedTopic):
    """標準的な画面遷移・ウィンドウ操作用のPubSubトピック列挙型。"""
    SWITCH_CONTAINER = auto()
    OPEN_SUBWINDOW = auto()
    CLOSE_SUBWINDOW = auto()
    CLOSE_ALL_SUBWINDOWS = auto()

class DefaultUpdateTopic(AutoNamedTopic):
    """標準的な状態更新通知用のPubSubトピック列挙型。"""
    UPDATE_STATE = auto()
    ADD_TO_LIST = auto()
    STATE_CHANGED = auto()
    STATE_ADDED = auto()

class DefaultProcessorTopic(AutoNamedTopic):
    """標準的なプロセッサ管理のPubSubトピック列挙型。"""
    REGISTOR_PROCESSOR = auto()
    DELETE_PROCESSOR = auto()
```

## State Management Best Practices

### State Definition (User Code)
```python
from pydantic import BaseModel
from typing import List, Optional

class AppState(BaseModel):
    count: int = 0
    items: List[str] = []
    user: Optional[dict] = None
```

### State Path Usage (RECOMMENDED)
```python
# ✅ RECOMMENDED: Use state proxy for IDE support
self.pub_update_state(str(self.store.state.count), new_value)
self.pub_add_to_list(str(self.store.state.items), new_item)
self.sub_state_changed(str(self.store.state.user), self.on_user_changed)

# ✅ Also acceptable: Direct string paths
self.pub_update_state("count", new_value)
self.sub_state_changed("user.name", self.on_name_changed)

# The state proxy provides IDE autocomplete and "Go to Definition" support
```

### Built-in Method Usage (RECOMMENDED)
```python
# ✅ RECOMMENDED: Use built-in convenience methods
class MyContainer(ContainerComponentTk[AppState]):
    def some_action(self):
        # Use built-in methods - they're designed for ease of use
        self.pub_update_state(str(self.store.state.count), 42)
        self.pub_switch_container(OtherContainer)
        self.pub_open_subwindow(DialogContainer)

# ❌ NOT RECOMMENDED: Manual topic publishing
class MyContainer(ContainerComponentTk[AppState]):
    def some_action(self):
        # Don't do this - use the built-in methods instead
        self.publish(DefaultUpdateTopic.UPDATE_STATE, state_path="count", new_value=42)
```

## Debug Support

```python
def enable_pubsub_debug_logging(level: int = logging.DEBUG) -> None:
    """PubSubのデバッグログを有効化する。"""
    ...

def disable_pubsub_debug_logging() -> None:
    """PubSubのデバッグログを無効化する。"""
    ...
```

## Type Safety Guidelines

### Always Use Generic Type Parameters
```python
# ✅ Correct
class MyContainer(ContainerComponentTtk[AppState]): ...
class MyProcessor(ProcessorBase[AppState]): ...
class MyApp(TkApplication[AppState]): ...

# ❌ Wrong - Missing type parameters
class MyContainer(ContainerComponentTtk): ...
```

### State Proxy for IDE Support
The state proxy system enables IDE features like autocomplete and "Go to Definition":

```python
# The proxy validates paths at runtime and provides string representation
path = str(self.store.state.user.email)  # -> "user.email"
self.pub_update_state(path, "new@email.com")

# IDE can navigate to AppState.user.email definition
# IDE provides autocomplete for available fields
```

## Dependencies
- `pydantic`: State modeling and validation
- `pypubsub`: Internal PubSub implementation
- `ttkthemes`: Themed application support (optional)
- `tkinter`: GUI framework (built into Python)