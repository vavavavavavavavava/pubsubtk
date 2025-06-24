# Storybookガイド

PubSubTk Storybookは、UIコンポーネントを独立して開発・テストできる開発環境です。React Storybookにインスパイアされ、Tkinter向けに最適化されています。

## 📚 Storybookとは

Storybookを使うと：

- コンポーネントを独立した環境で開発
- 動的なKnobコントロールでリアルタイムにプロパティを変更
- 再利用可能なコンポーネントライブラリの構築
- デザイナーとの協業がスムーズに

## 🚀 クイックスタート

### 最小限のStorybook

```python
from pubsubtk.storybook import story, StorybookApplication

@story("Hello.World")
def hello_world(ctx):
    import tkinter as tk
    label = tk.Label(ctx.parent, text="Hello, Storybook!")
    label.pack()
    return label

if __name__ == "__main__":
    app = StorybookApplication()
    app.run()
```

### Knobを使った動的コントロール

```python
@story("Button.Dynamic")
def dynamic_button(ctx):
    import tkinter as tk
    
    # Knobでプロパティを動的に制御
    text = ctx.knob("text", str, "Click me!")
    bg_color = ctx.knob("bgColor", str, "#007bff", 
                        choices=["#007bff", "#28a745", "#dc3545", "#ffc107"])
    enabled = ctx.knob("enabled", bool, True)
    
    btn = tk.Button(
        ctx.parent,
        text=text.value,
        bg=bg_color.value,
        fg="white",
        state="normal" if enabled.value else "disabled"
    )
    btn.pack(padx=20, pady=20)
    
    # Knob変更時の自動更新
    text.add_change_callback(lambda v: btn.config(text=v))
    bg_color.add_change_callback(lambda v: btn.config(bg=v))
    enabled.add_change_callback(
        lambda v: btn.config(state="normal" if v else "disabled")
    )
    
    return btn
```

## 📝 ストーリーの定義

### @storyデコレータ

```python
@story(path="Category.Subcategory", title="My Component")
def my_story(ctx: StoryContext):
    # コンポーネントを作成して返す
    pass
```

- `path`: ドット区切りの階層パス（省略時は関数名から自動生成）
- `title`: 表示名（省略時はパスの最後の要素）
- `ctx`: StoryContextオブジェクト（親Widget、Knob機能を提供）

### 階層構造の作成

```python
# Buttons カテゴリ
@story("Buttons.Primary")
def primary_button(ctx): ...

@story("Buttons.Secondary")
def secondary_button(ctx): ...

@story("Buttons.Danger")
def danger_button(ctx): ...

# Forms カテゴリ
@story("Forms.TextField")
def text_field(ctx): ...

@story("Forms.Checkbox")
def checkbox(ctx): ...
```

## 🎛️ Knobコントロール

### 基本的なKnob

```python
# テキスト
text = ctx.knob("label", str, "Default Text")

# 数値
size = ctx.knob("size", int, 12, range_=(8, 48))

# ブール値
enabled = ctx.knob("enabled", bool, True)

# 選択肢
color = ctx.knob("color", str, "blue", 
                choices=["red", "green", "blue", "yellow"])

# 複数行テキスト
content = ctx.knob("content", str, "Line 1\nLine 2", multiline=True)
```

### Knobパラメータ

- `name`: Knobの名前（一意である必要があります）
- `type_`: 値の型（str, int, float, bool）
- `default`: デフォルト値
- `desc`: 説明文（省略可）
- `range_`: 数値の範囲（tuple）
- `choices`: 選択肢のリスト
- `multiline`: 複数行入力（strのみ）

### 値の永続化

Knobの値は自動的に保存され、同じストーリーを再度開いたときに復元されます。

## 🔧 PubSubTkコンポーネントの使用

### Presentationalコンポーネント

```python
from pubsubtk import PresentationalComponentTk

class Card(PresentationalComponentTk):
    def setup_ui(self):
        import tkinter as tk
        self.title_label = tk.Label(self, font=("Arial", 14, "bold"))
        self.title_label.pack()
        self.content_label = tk.Label(self)
        self.content_label.pack()
        
    def set_data(self, title: str, content: str):
        self.title_label.config(text=title)
        self.content_label.config(text=content)

@story("Components.Card")
def card_story(ctx):
    title = ctx.knob("title", str, "Card Title")
    content = ctx.knob("content", str, "Card content goes here")
    
    card = Card(ctx.parent)
    card.set_data(title.value, content.value)
    card.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Knob変更時の更新
    title.add_change_callback(
        lambda v: card.set_data(v, content.value)
    )
    content.add_change_callback(
        lambda v: card.set_data(title.value, v)
    )
    
    return card
```

### Containerコンポーネント（状態付き）

```python
from pubsubtk import ContainerComponentTk, get_store
from pydantic import BaseModel

class CounterState(BaseModel):
    count: int = 0

class Counter(ContainerComponentTk[CounterState]):
    def setup_ui(self):
        import tkinter as tk
        self.label = tk.Label(self, font=("Arial", 24))
        self.label.pack()
        tk.Button(self, text="Increment", command=self.increment).pack()
        
    def setup_subscriptions(self):
        self.sub_for_refresh(self.store.state.count, self.update_display)
        
    def refresh_from_state(self):
        self.update_display()
        
    def update_display(self):
        self.label.config(text=str(self.store.get_current_state().count))
        
    def increment(self):
        state = self.store.get_current_state()
        self.pub_update_state(self.store.state.count, state.count + 1)

@story("Components.Counter")
def counter_story(ctx):
    initial = ctx.knob("initial", int, 0, range_=(-10, 10))
    
    # ローカルストアを作成
    store = get_store(CounterState)
    store.update_state("count", initial.value)
    
    counter = Counter(ctx.parent, store=store)
    counter.pack(padx=40, pady=40)
    
    return counter
```

## 🗂️ ストーリーの自動検出

プロジェクトが大きくなると、ストーリーを手動でインポートするのは大変です。`auto_discover`を使うと自動検出できます：

```python
# run_storybook.py
from pubsubtk.storybook import StorybookApplication
from pubsubtk.storybook.core.auto_discover import discover_stories

if __name__ == "__main__":
    # src/以下の全ての@storyを自動検出
    discover_stories("src")
    
    app = StorybookApplication(
        theme="arc",
        title="My Component Library"
    )
    app.run()
```

## 🎨 カスタマイズ

### テーマの変更

```python
app = StorybookApplication(theme="clam")  # arc, clam, alt, default, classic
```

### ウィンドウサイズ

```python
app = StorybookApplication(geometry="1600x1000")
```

### 手動セットアップ

```python
app = StorybookApplication(auto_setup=False)
# カスタム初期化処理
app.switch_container(CustomStorybookContainer)
app.run()
```

## 💡 ベストプラクティス

### 1. ストーリーの整理

```
components/
├── buttons/
│   ├── __init__.py
│   ├── primary_button.py    # コンポーネント定義
│   └── stories.py           # @story定義
├── forms/
│   ├── __init__.py
│   ├── text_field.py
│   └── stories.py
└── run_storybook.py
```

### 2. Knobの適切な使用

```python
@story("Forms.Input")
def input_story(ctx):
    # ✅ 良い例：関連するプロパティをKnobに
    placeholder = ctx.knob("placeholder", str, "Enter text...")
    max_length = ctx.knob("maxLength", int, 100, range_=(10, 500))
    
    # ❌ 悪い例：内部状態をKnobにしない
    # current_text = ctx.knob("currentText", str, "")  # これは避ける
```

### 3. ストーリーの分離

```python
# ✅ 各バリエーションを別ストーリーに
@story("Button.Primary.Normal")
def primary_normal(ctx): ...

@story("Button.Primary.Disabled")
def primary_disabled(ctx): ...

@story("Button.Primary.Loading")
def primary_loading(ctx): ...
```

## 🔍 トラブルシューティング

### Knobの値が保持されない

- 同じ`name`のKnobが複数ある場合、値が混在します
- ストーリーごとに一意の名前を使用してください

### ストーリーが表示されない

- `@story`デコレータが正しく適用されているか確認
- `auto_discover`を使用している場合、パスが正しいか確認
- ファイルにシンタックスエラーがないか確認

### パフォーマンスの問題

- Knobの`add_change_callback`で重い処理を避ける
- デバウンス処理を検討（Knobコントロールには組み込みのデバウンスがあります）

## 📖 関連リンク

- [コンポーネント開発レシピ](cookbook.md#storybook-でのコンポーネント開発)
- [Storybookサンプル](examples.md#4-storybookを使ったコンポーネントカタログ)
- [APIリファレンス - Storybook](api/pubsubtk/storybook/)
