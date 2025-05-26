# PubSubTk Library - Quick Start Guide

## Installation & Basic Usage
```python
from pydantic import BaseModel
from typing import List
import tkinter as tk
from pubsubtk import TkApplication, ContainerComponentTk, get_store, enable_pubsub_debug_logging

# 1. Define your application state
class AppState(BaseModel):
    count: int = 0
    items: List[str] = []

# 2. Create main UI container
class MainView(ContainerComponentTk[AppState]):
    def setup_ui(self):
        self.label = tk.Label(self, text="Count: 0")
        self.btn_inc = tk.Button(self, text="+", command=self.increment)
        self.btn_dec = tk.Button(self, text="-", command=self.decrement)
        
        self.label.pack(pady=10)
        self.btn_inc.pack(side=tk.LEFT, padx=5)
        self.btn_dec.pack(side=tk.LEFT, padx=5)
    
    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.count, self.on_count_changed)
    
    def refresh_from_state(self):
        count = self.store.get_current_state().count
        self.label.config(text=f"Count: {count}")
    
    def increment(self):
        current = self.store.get_current_state().count
        self.pub_update_state(self.store.state.count, current + 1)
    
    def decrement(self):
        current = self.store.get_current_state().count
        self.pub_update_state(self.store.state.count, current - 1)
    
    def on_count_changed(self, old_value, new_value):
        self.refresh_from_state()

# 3. Create and run app
if __name__ == "__main__":
    # Optional: Enable debug logging
    # enable_pubsub_debug_logging()
    
    app = TkApplication(AppState, title="Counter App")
    app.pub_switch_container(MainView)
    app.run()
```

## Core Concepts

### State Management
```python
from pydantic import BaseModel

class TodoItem(BaseModel):
    id: int
    text: str
    done: bool = False

class AppState(BaseModel):
    todos: List[TodoItem] = []
    filter: str = "all"
```

### Component Types

**Container Components** (Stateful):
```python
from pubsubtk import ContainerComponentTk, ContainerComponentTtk

class TodoList(ContainerComponentTk[AppState]):
    def setup_ui(self):           # Create widgets
    def setup_subscriptions(self): # Listen to state changes  
    def refresh_from_state(self):  # Update UI from state
```

**Presentational Components** (Stateless):
```python
from pubsubtk import PresentationalComponentTk

class UserCard(PresentationalComponentTk):
    def setup_ui(self):              # Create widgets
    def update_data(self, **data):   # Update with external data
```

**Processors** (Business Logic):
```python
from pubsubtk import ProcessorBase

class TodoProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):   # Handle business events
```

### Application Types
```python
from pubsubtk import TkApplication, ThemedApplication

# Standard Tkinter
app = TkApplication(AppState, title="My App")

# Themed ttk
app = ThemedApplication(AppState, theme="arc", title="My App")

app.pub_switch_container(MainView)
app.run()
```

## Essential Operations

### State Updates
```python
# Update single field
self.pub_update_state(self.store.state.count, 42)

# Add to list
self.pub_add_to_list(self.store.state.todos, new_todo)

# Get current state
state = self.store.get_current_state()
```

### Listen to Changes
```python
def setup_subscriptions(self):
    # Listen to specific field
    self.sub_state_changed(self.store.state.count, self.on_count_changed)
    
    # Listen to list additions
    self.sub_state_added(self.store.state.todos, self.on_todo_added)

def on_count_changed(self, old_value, new_value):
    self.refresh_from_state()
```

### Navigation
```python
# Switch main content
self.pub_switch_container(SettingsView)

# Open dialog/popup
self.pub_open_subwindow(AboutDialog, win_id="about")

# Close specific window
self.pub_close_subwindow("about")
```

### Business Logic
```python
from pubsubtk import ProcessorBase

class TodoProcessor(ProcessorBase[AppState]):
    def setup_subscriptions(self):
        self.subscribe("todo.toggle", self.toggle_todo)
        self.subscribe("todo.delete", self.delete_todo)
    
    def toggle_todo(self, todo_id: int):
        # Business logic here
        pass

# Register processor
app.pub_registor_processor(TodoProcessor)
```

## Complete Todo App
```python
from pydantic import BaseModel
from typing import List
import tkinter as tk
from pubsubtk import TkApplication, ContainerComponentTk

class TodoItem(BaseModel):
    id: int
    text: str
    done: bool = False

class AppState(BaseModel):
    todos: List[TodoItem] = []
    next_id: int = 1

class TodoApp(ContainerComponentTk[AppState]):
    def setup_ui(self):
        self.entry = tk.Entry(self)
        self.add_btn = tk.Button(self, text="Add", command=self.add_todo)
        self.listbox = tk.Listbox(self)
        
        self.entry.pack(fill=tk.X, padx=5, pady=5)
        self.add_btn.pack(pady=5)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_subscriptions(self):
        self.sub_state_changed(self.store.state.todos, self.refresh_from_state)
    
    def refresh_from_state(self):
        self.listbox.delete(0, tk.END)
        for todo in self.store.get_current_state().todos:
            status = "✓" if todo.done else "○"
            self.listbox.insert(tk.END, f"{status} {todo.text}")
    
    def add_todo(self):
        text = self.entry.get().strip()
        if text:
            state = self.store.get_current_state()
            new_todo = TodoItem(id=state.next_id, text=text)
            self.pub_add_to_list(self.store.state.todos, new_todo)
            self.pub_update_state(self.store.state.next_id, state.next_id + 1)
            self.entry.delete(0, tk.END)

if __name__ == "__main__":
    app = TkApplication(AppState, title="Todo App")
    app.pub_switch_container(TodoApp)
    app.run()
```

## Key Rules

1. **Use generics**: `ContainerComponentTk[YourState]`, `TkApplication(YourState)`  
2. **State paths**: Use `self.store.state.field` directly, wrap with `str()` when doing string operations
3. **Built-in methods**: Use `pub_*` and `sub_*` methods, not manual topics
4. **State proxy**: Enables autocomplete and "Go to Definition"

### State Path Usage
```python
# ✅ Direct usage - recommended
self.pub_update_state(self.store.state.count, new_value)
self.sub_state_changed(self.store.state.user.name, handler)

# ✅ Wrap with str() when doing string operations 
path = str(self.store.state.user.name) + "_backup"  # Avoid .join() etc on proxy
base_path = str(self.store.state.items)
full_path = f"{base_path}.{index}"

# ❌ Don't do string operations directly on proxy
# self.store.state.user.name.join(...)  # Error: state has no 'join' method
```

## Debug
```python
from pubsubtk import enable_pubsub_debug_logging
enable_pubsub_debug_logging()  # See all PubSub messages
```

Start building reactive, type-safe Tkinter apps!