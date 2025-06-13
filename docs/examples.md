# Examples

PubSubTkを使った様々なアプリケーションの実装例を紹介します。

## 📋 Todo アプリケーション

状態管理、リスト操作、画面遷移を含む実用的な例です。

### 状態定義

```python
from pydantic import BaseModel
from typing import List
from enum import Enum

class TodoStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"

class TodoItem(BaseModel):
    id: int
    text: str
    status: TodoStatus = TodoStatus.ACTIVE
    created_at: str = ""

class FilterMode(str, Enum):
    ALL = "all"
    ACTIVE = "active" 
    COMPLETED = "completed"

class TodoState(BaseModel):
    todos: List[TodoItem] = []
    next_id: int = 1
    filter_mode: FilterMode = FilterMode.ALL
    input_text: str = ""
```

### ビジネスロジック（Processor）

```python
from pubsubtk import ProcessorBase, AutoNamedTopic
from enum import auto
from datetime import datetime

class TodoEvents(AutoNamedTopic):
    ADD_TODO = auto()
    TOGGLE_TODO = auto()
    DELETE_TODO = auto()
    SET_FILTER = auto()
    CLEAR_COMPLETED = auto()

class TodoProcessor(ProcessorBase[TodoState]):
    def setup_subscriptions(self):
        self.subscribe(TodoEvents.ADD_TODO, self.handle_add_todo)
        self.subscribe(TodoEvents.TOGGLE_TODO, self.handle_toggle_todo)
        self.subscribe(TodoEvents.DELETE_TODO, self.handle_delete_todo)
        self.subscribe(TodoEvents.SET_FILTER, self.handle_set_filter)
        self.subscribe(TodoEvents.CLEAR_COMPLETED, self.handle_clear_completed)

    def handle_add_todo(self, text: str):
        if not text.strip():
            return
            
        state = self.store.get_current_state()
        new_todo = TodoItem(
            id=state.next_id,
            text=text.strip(),
            status=TodoStatus.ACTIVE,
            created_at=datetime.now().isoformat()
        )
        
        self.pub_add_to_list(self.store.state.todos, new_todo)
        self.pub_update_state(self.store.state.next_id, state.next_id + 1)
        self.pub_update_state(self.store.state.input_text, "")

    def handle_toggle_todo(self, todo_id: int):
        state = self.store.get_current_state()
        updated_todos = []
        
        for todo in state.todos:
            if todo.id == todo_id:
                new_status = (TodoStatus.COMPLETED 
                            if todo.status == TodoStatus.ACTIVE 
                            else TodoStatus.ACTIVE)
                updated_todo = todo.model_copy()
                updated_todo.status = new_status
                updated_todos.append(updated_todo)
            else:
                updated_todos.append(todo)
        
        self.pub_update_state(self.store.state.todos, updated_todos)

    def handle_delete_todo(self, todo_id: int):
        state = self.store.get_current_state()
        updated_todos = [todo for todo in state.todos if todo.id != todo_id]
        self.pub_update_state(self.store.state.todos, updated_todos)

    def handle_set_filter(self, filter_mode: FilterMode):
        self.pub_update_state(self.store.state.filter_mode, filter_mode)

    def handle_clear_completed(self):
        state = self.store.get_current_state()
        active_todos = [todo for todo in state.todos 
                       if todo.status == TodoStatus.ACTIVE]
        self.pub_update_state(self.store.state.todos, active_todos)
```

### 表示コンポーネント（Presentational）

```python
from pubsubtk import PresentationalComponentTk
import tkinter as tk

class TodoItemView(PresentationalComponentTk):
    def setup_ui(self):
        self.configure(relief=tk.RAISED, borderwidth=1, padx=5, pady=3)
        
        # チェックボックス
        self.var = tk.BooleanVar()
        self.checkbox = tk.Checkbutton(
            self, 
            variable=self.var, 
            command=self.on_toggle
        )
        self.checkbox.pack(side=tk.LEFT)
        
        # テキストラベル
        self.label = tk.Label(self, text="", anchor="w")
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 削除ボタン
        self.delete_btn = tk.Button(
            self, 
            text="×", 
            width=3, 
            command=self.on_delete,
            fg="red"
        )
        self.delete_btn.pack(side=tk.RIGHT)

    def update_data(self, todo: TodoItem):
        self.todo = todo
        self.var.set(todo.status == TodoStatus.COMPLETED)
        
        # 完了済みのスタイル
        if todo.status == TodoStatus.COMPLETED:
            text = f"✓ {todo.text}"
            fg_color = "gray"
        else:
            text = todo.text
            fg_color = "black"
            
        self.label.config(text=text, fg=fg_color)

    def on_toggle(self):
        self.trigger_event("toggle", todo_id=self.todo.id)

    def on_delete(self):
        self.trigger_event("delete", todo_id=self.todo.id)

class FilterButtonsView(PresentationalComponentTk):
    def setup_ui(self):
        self.buttons = {}
        
        for filter_mode in FilterMode:
            btn = tk.Button(
                self, 
                text=filter_mode.value.title(),
                command=lambda fm=filter_mode: self.on_filter_change(fm)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.buttons[filter_mode] = btn

    def update_active_filter(self, current_filter: FilterMode):
        for filter_mode, button in self.buttons.items():
            if filter_mode == current_filter:
                button.config(relief=tk.SUNKEN, bg="lightblue")
            else:
                button.config(relief=tk.RAISED, bg="SystemButtonFace")

    def on_filter_change(self, filter_mode: FilterMode):
        self.trigger_event("filter_change", filter_mode=filter_mode)
```

### メインコンテナ（Container）

```python
from pubsubtk import ContainerComponentTk
import tkinter as tk

class TodoContainer(ContainerComponentTk[TodoState]):
    def setup_ui(self):
        # タイトル
        title_label = tk.Label(self, text="📋 Todo App", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        
        # 入力エリア
        input_frame = tk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.entry = tk.Entry(input_frame, font=("Arial", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", self.on_add_todo)
        
        add_btn = tk.Button(input_frame, text="追加", command=self.on_add_todo)
        add_btn.pack(side=tk.RIGHT)
        
        # フィルターボタン
        filter_frame = tk.Frame(self)
        filter_frame.pack(pady=10)
        
        tk.Label(filter_frame, text="表示:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_view = FilterButtonsView(filter_frame)
        self.filter_view.pack(side=tk.LEFT)
        self.filter_view.register_handler("filter_change", self.on_filter_change)
        
        # 一括操作
        action_frame = tk.Frame(self)
        action_frame.pack(pady=5)
        
        clear_btn = tk.Button(action_frame, text="完了済みを削除", 
                             command=self.on_clear_completed)
        clear_btn.pack()
        
        # Todoリスト
        list_frame = tk.Frame(self, relief=tk.SUNKEN, borderwidth=2)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # スクロール可能エリア
        canvas = tk.Canvas(list_frame)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", 
                                command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.todo_widgets = {}

    def setup_subscriptions(self):
        self.sub_for_refresh(self.store.state.todos, self.refresh_todo_list)
        self.sub_for_refresh(self.store.state.filter_mode, self.refresh_filter_buttons)
        self.sub_state_changed(self.store.state.input_text, self.on_input_changed)

    def refresh_from_state(self):
        self.refresh_todo_list()
        self.refresh_filter_buttons()
        state = self.store.get_current_state()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, state.input_text)

    def refresh_todo_list(self):
        # 既存ウィジェットをクリア
        for widget in self.todo_widgets.values():
            widget.destroy()
        self.todo_widgets.clear()
        
        state = self.store.get_current_state()
        
        # フィルタリング
        if state.filter_mode == FilterMode.ACTIVE:
            filtered_todos = [t for t in state.todos 
                            if t.status == TodoStatus.ACTIVE]
        elif state.filter_mode == FilterMode.COMPLETED:
            filtered_todos = [t for t in state.todos 
                            if t.status == TodoStatus.COMPLETED]
        else:  # ALL
            filtered_todos = state.todos
        
        # Todoアイテムを表示
        for todo in filtered_todos:
            todo_widget = TodoItemView(self.scrollable_frame)
            todo_widget.pack(fill=tk.X, padx=5, pady=2)
            todo_widget.update_data(todo)
            
            # イベントハンドラ登録
            todo_widget.register_handler("toggle", self.on_toggle_todo)
            todo_widget.register_handler("delete", self.on_delete_todo)
            
            self.todo_widgets[todo.id] = todo_widget

    def refresh_filter_buttons(self):
        state = self.store.get_current_state()
        self.filter_view.update_active_filter(state.filter_mode)

    def on_input_changed(self, old_value, new_value):
        if new_value != self.entry.get():
            self.entry.delete(0, tk.END)
            self.entry.insert(0, new_value)

    def on_add_todo(self, event=None):
        text = self.entry.get().strip()
        if text:
            self.publish(TodoEvents.ADD_TODO, text=text)

    def on_toggle_todo(self, todo_id: int):
        self.publish(TodoEvents.TOGGLE_TODO, todo_id=todo_id)

    def on_delete_todo(self, todo_id: int):
        self.publish(TodoEvents.DELETE_TODO, todo_id=todo_id)

    def on_filter_change(self, filter_mode: FilterMode):
        self.publish(TodoEvents.SET_FILTER, filter_mode=filter_mode)

    def on_clear_completed(self):
        self.publish(TodoEvents.CLEAR_COMPLETED)
```

### アプリケーション起動

```python
from pubsubtk import TkApplication

if __name__ == "__main__":
    app = TkApplication(TodoState, title="Todo App", geometry="600x500")
    app.pub_register_processor(TodoProcessor)
    app.switch_container(TodoContainer)
    app.run()
```

## 📊 データビューア

CSV/JSONファイルを読み込んで表示・編集するアプリケーション。

### 状態定義

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DataRow(BaseModel):
    id: int
    data: Dict[str, Any]

class DataViewerState(BaseModel):
    file_path: Optional[str] = None
    columns: List[str] = []
    rows: List[DataRow] = []
    selected_row_id: Optional[int] = None
    filter_text: str = ""
    sort_column: Optional[str] = None
    sort_ascending: bool = True
```

### ファイル操作Processor

```python
import csv
import json
from pathlib import Path
from tkinter import filedialog

class DataViewerEvents(AutoNamedTopic):
    LOAD_FILE = auto()
    SAVE_FILE = auto()
    FILTER_DATA = auto()
    SORT_DATA = auto()
    SELECT_ROW = auto()

class FileProcessor(ProcessorBase[DataViewerState]):
    def setup_subscriptions(self):
        self.subscribe(DataViewerEvents.LOAD_FILE, self.handle_load_file)
        self.subscribe(DataViewerEvents.SAVE_FILE, self.handle_save_file)
        self.subscribe(DataViewerEvents.FILTER_DATA, self.handle_filter_data)
        self.subscribe(DataViewerEvents.SORT_DATA, self.handle_sort_data)

    def handle_load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            path = Path(file_path)
            
            if path.suffix.lower() == '.csv':
                self.load_csv(file_path)
            elif path.suffix.lower() == '.json':
                self.load_json(file_path)
                
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")

    def load_csv(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []
            
            rows = []
            for i, row_data in enumerate(reader):
                rows.append(DataRow(id=i, data=dict(row_data)))
        
        self.pub_update_state(self.store.state.file_path, file_path)
        self.pub_update_state(self.store.state.columns, columns)
        self.pub_update_state(self.store.state.rows, rows)

    def load_json(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list) and data:
            # 最初の行からカラムを推定
            columns = list(data[0].keys()) if data else []
            
            rows = []
            for i, row_data in enumerate(data):
                rows.append(DataRow(id=i, data=row_data))
            
            self.pub_update_state(self.store.state.file_path, file_path)
            self.pub_update_state(self.store.state.columns, columns)
            self.pub_update_state(self.store.state.rows, rows)
```

### データ表示Container

```python
from tkinter import ttk

class DataViewerContainer(ContainerComponentTk[DataViewerState]):
    def setup_ui(self):
        # ツールバー
        toolbar = tk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="📂 ファイルを開く", 
                 command=self.load_file).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="💾 保存", 
                 command=self.save_file).pack(side=tk.LEFT, padx=2)
        
        # フィルター
        tk.Label(toolbar, text="フィルター:").pack(side=tk.LEFT, padx=(10, 2))
        self.filter_entry = tk.Entry(toolbar, width=20)
        self.filter_entry.pack(side=tk.LEFT, padx=2)
        self.filter_entry.bind("<KeyRelease>", self.on_filter_change)
        
        # データテーブル
        table_frame = tk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeviewでテーブル表示
        self.tree = ttk.Treeview(table_frame, show="headings")
        
        # スクロールバー
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", 
                                   command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", 
                                   command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # レイアウト
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # イベントバインディング
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        self.tree.bind("<Double-1>", self.on_row_double_click)

    def setup_subscriptions(self):
        self.sub_for_refresh(self.store.state.columns, self.refresh_table)
        self.sub_for_refresh(self.store.state.rows, self.refresh_table)
        self.sub_state_changed(self.store.state.file_path, self.on_file_changed)

    def refresh_from_state(self):
        self.refresh_table()

    def refresh_table(self):
        state = self.store.get_current_state()
        
        # 既存の列とデータをクリア
        for col in self.tree["columns"]:
            self.tree.delete(col)
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not state.columns:
            return
            
        # 列の設定
        self.tree["columns"] = state.columns
        for col in state.columns:
            self.tree.heading(col, text=col, 
                            command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=100, minwidth=50)
        
        # データの追加
        filtered_rows = self.filter_rows(state.rows, state.filter_text)
        for row in filtered_rows:
            values = [row.data.get(col, "") for col in state.columns]
            self.tree.insert("", "end", iid=row.id, values=values)

    def filter_rows(self, rows: List[DataRow], filter_text: str) -> List[DataRow]:
        if not filter_text:
            return rows
            
        filter_lower = filter_text.lower()
        filtered = []
        
        for row in rows:
            # すべての値に対してフィルタを適用
            for value in row.data.values():
                if filter_lower in str(value).lower():
                    filtered.append(row)
                    break
        
        return filtered

    def on_file_changed(self, old_path, new_path):
        if new_path:
            self.master.master.title(f"Data Viewer - {Path(new_path).name}")
        else:
            self.master.master.title("Data Viewer")

    def on_filter_change(self, event=None):
        filter_text = self.filter_entry.get()
        self.pub_update_state(self.store.state.filter_text, filter_text)
        self.refresh_table()

    def on_row_select(self, event):
        selection = self.tree.selection()
        if selection:
            row_id = int(selection[0])
            self.publish(DataViewerEvents.SELECT_ROW, row_id=row_id)

    def on_row_double_click(self, event):
        # 選択された行の編集ダイアログを開く
        selection = self.tree.selection()
        if selection:
            row_id = int(selection[0])
            self.open_edit_dialog(row_id)

    def sort_by_column(self, column: str):
        self.publish(DataViewerEvents.SORT_DATA, column=column)

    def load_file(self):
        self.publish(DataViewerEvents.LOAD_FILE)

    def save_file(self):
        self.publish(DataViewerEvents.SAVE_FILE)

# アプリケーション起動
if __name__ == "__main__":
    app = TkApplication(DataViewerState, title="Data Viewer", geometry="800x600")
    app.pub_register_processor(FileProcessor)
    app.switch_container(DataViewerContainer)
    app.run()
```

## 🎮 ゲーム: シンプルなマインスイーパー

```python
import random
from enum import Enum

class CellState(str, Enum):
    HIDDEN = "hidden"
    REVEALED = "revealed"
    FLAGGED = "flagged"

class GameStatus(str, Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"

class Cell(BaseModel):
    x: int
    y: int
    is_mine: bool = False
    adjacent_mines: int = 0
    state: CellState = CellState.HIDDEN

class MinesweeperState(BaseModel):
    width: int = 10
    height: int = 10
    mine_count: int = 10
    cells: List[List[Cell]] = []
    game_status: GameStatus = GameStatus.PLAYING
    flags_remaining: int = 10
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class MinesweeperEvents(AutoNamedTopic):
    NEW_GAME = auto()
    REVEAL_CELL = auto()
    FLAG_CELL = auto()
    AUTO_REVEAL = auto()

class MinesweeperProcessor(ProcessorBase[MinesweeperState]):
    def setup_subscriptions(self):
        self.subscribe(MinesweeperEvents.NEW_GAME, self.handle_new_game)
        self.subscribe(MinesweeperEvents.REVEAL_CELL, self.handle_reveal_cell)
        self.subscribe(MinesweeperEvents.FLAG_CELL, self.handle_flag_cell)

    def handle_new_game(self, width: int = 10, height: int = 10, mine_count: int = 10):
        # ゲームボードの初期化
        cells = [[Cell(x=x, y=y) for x in range(width)] for y in range(height)]
        
        # 地雷を配置
        positions = [(x, y) for x in range(width) for y in range(height)]
        mine_positions = random.sample(positions, mine_count)
        
        for x, y in mine_positions:
            cells[y][x].is_mine = True
        
        # 隣接地雷数を計算
        for y in range(height):
            for x in range(width):
                if not cells[y][x].is_mine:
                    cells[y][x].adjacent_mines = self.count_adjacent_mines(cells, x, y)
        
        new_state = MinesweeperState(
            width=width,
            height=height,
            mine_count=mine_count,
            cells=cells,
            flags_remaining=mine_count,
            start_time=time.time()
        )
        
        self.pub_replace_state(new_state)

    def count_adjacent_mines(self, cells: List[List[Cell]], x: int, y: int) -> int:
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if (0 <= nx < len(cells[0]) and 0 <= ny < len(cells) and 
                    cells[ny][nx].is_mine):
                    count += 1
        return count

# セルビュー（Presentational）
class CellView(PresentationalComponentTk):
    def setup_ui(self):
        self.button = tk.Button(
            self, 
            width=2, 
            height=1,
            font=("Courier", 12, "bold"),
            command=self.on_left_click
        )
        self.button.pack(fill=tk.BOTH, expand=True)
        self.button.bind("<Button-3>", self.on_right_click)  # 右クリック

    def update_cell(self, cell: Cell):
        self.cell = cell
        
        if cell.state == CellState.HIDDEN:
            self.button.config(text="", bg="SystemButtonFace", relief=tk.RAISED)
        elif cell.state == CellState.FLAGGED:
            self.button.config(text="🚩", bg="yellow", relief=tk.RAISED)
        elif cell.state == CellState.REVEALED:
            if cell.is_mine:
                self.button.config(text="💣", bg="red", relief=tk.SUNKEN)
            else:
                text = str(cell.adjacent_mines) if cell.adjacent_mines > 0 else ""
                colors = ["", "blue", "green", "red", "purple", "maroon", "turquoise", "black", "gray"]
                color = colors[cell.adjacent_mines] if cell.adjacent_mines < len(colors) else "black"
                self.button.config(text=text, bg="lightgray", fg=color, relief=tk.SUNKEN)

    def on_left_click(self):
        if hasattr(self, 'cell'):
            self.trigger_event("reveal", x=self.cell.x, y=self.cell.y)

    def on_right_click(self, event):
        if hasattr(self, 'cell'):
            self.trigger_event("flag", x=self.cell.x, y=self.cell.y)
```

## 🛠️ 設定アプリ

アプリケーション設定を管理するGUIアプリケーション。

```python
class SettingsState(BaseModel):
    appearance: dict = {
        "theme": "light",
        "font_size": 12,
        "window_size": "800x600"
    }
    behavior: dict = {
        "auto_save": True,
        "confirm_exit": False,
        "startup_screen": "dashboard"
    }
    advanced: dict = {
        "debug_mode": False,
        "log_level": "INFO",
        "cache_size": 100
    }

class SettingsContainer(ContainerComponentTk[SettingsState]):
    def setup_ui(self):
        # タブ式インターフェース
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 外観タブ
        appearance_frame = ttk.Frame(notebook)
        notebook.add(appearance_frame, text="外観")
        self.setup_appearance_tab(appearance_frame)
        
        # 動作タブ
        behavior_frame = ttk.Frame(notebook)
        notebook.add(behavior_frame, text="動作")
        self.setup_behavior_tab(behavior_frame)
        
        # 高度な設定タブ
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="高度な設定")
        self.setup_advanced_tab(advanced_frame)
        
        # ボタンエリア
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(button_frame, text="適用", command=self.apply_settings).pack(side=tk.RIGHT, padx=2)
        tk.Button(button_frame, text="リセット", command=self.reset_settings).pack(side=tk.RIGHT, padx=2)

    def setup_appearance_tab(self, parent):
        # テーマ選択
        theme_frame = tk.Frame(parent)
        theme_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(theme_frame, text="テーマ:").pack(side=tk.LEFT)
        self.theme_var = tk.StringVar()
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                  values=["light", "dark", "auto"])
        theme_combo.pack(side=tk.LEFT, padx=5)
        
        # フォントサイズ
        font_frame = tk.Frame(parent)
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(font_frame, text="フォントサイズ:").pack(side=tk.LEFT)
        self.font_size_var = tk.IntVar()
        font_spin = tk.Spinbox(font_frame, from_=8, to=24, textvariable=self.font_size_var)
        font_spin.pack(side=tk.LEFT, padx=5)
```

これらの例では、PubSubTkの主要な機能を実際のアプリケーションでどのように活用するかを示しています：

- **状態管理**: Pydanticモデルによる型安全な状態定義
- **コンポーネント分離**: Container/Presentational/Processorの適切な役割分担
- **イベント処理**: カスタムトピックによる疎結合な通信
- **UI更新**: 状態変更の自動検知とリアクティブ更新
- **複雑な機能**: ファイル操作、フィルタリング、ソート、ゲームロジックなど

各例をベースに、独自のアプリケーションを開発してみてください！
