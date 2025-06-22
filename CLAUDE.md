# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PubSubTk is an event-driven, state management Python GUI library that combines Tkinter/ttk with Publish-Subscribe patterns and Pydantic models. It follows a React-inspired architectural pattern with Container/Presentational/Processor three-layer separation.

## Development Commands

### Poetry (Dependency Management)

```bash
poetry install                 # Install dependencies
poetry add <package>          # Add new dependency
poetry run python <script>   # Run Python with project dependencies
```

### Documentation

```bash
poetry run mkdocs serve       # Serve docs locally at http://127.0.0.1:8000
poetry run mkdocs build       # Build documentation
poetry run python scripts/generate_docs.py  # Generate API reference docs
```

### Testing & Examples

```bash
poetry run python tests/sample_app/main.py   # Run comprehensive sample application
poetry run python -m src.pubsubtk.storybook.demo_storybook  # Run storybook demo
```

## Core Architecture

### Three-Layer Component Structure

1. **Container Components** (`src/pubsubtk/ui/base/container_base.py`)
   - State-aware components that subscribe to Store changes
   - Handle user interactions and coordinate business logic
   - Inherit from `ContainerBase` and use `@subscribe_to_store` decorator

2. **Presentational Components** (`src/pubsubtk/ui/base/presentational_base.py`)
   - Pure display components with no state dependencies
   - Event-based communication with Container components
   - Inherit from `PresentationalBase`

3. **Processor Components** (`src/pubsubtk/processor/processor_base.py`)
   - Business logic and complex state operations
   - Event-driven processing with Store integration
   - Inherit from `ProcessorBase` and register with application

### State Management Pattern

The Store (`src/pubsubtk/store/store.py`) is the single source of truth:

```python
# Define state model with Pydantic
class AppState(BaseModel):
    todos: List[Todo] = []
    current_user: Optional[str] = None

# Access state via StateProxy for IDE support
store.state.todos.append(new_todo)  # Full autocomplete and type checking

# Subscribe to specific state changes
@subscribe_to_store("todos")
def on_todos_changed(self, state: AppState):
    self.refresh_todo_list()
```

### Pub/Sub Communication

All components inherit from `PubSubBase` for decoupled communication:

```python
# Subscribe to topics
self.subscribe("navigation.show_page", self.handle_navigation)

# Publish events
self.publish("user.login", {"user_id": user.id})
```

## Key Patterns

### Application Structure

- Inherit from `TkApplication` or `ThemedApplication`
- Use Template components for layout with named slots
- Register Processors in `setup_processors()`
- Register UI containers in `setup_subscriptions()`

### Component Registration

```python
def setup_processors(self):
    self.register_processor(TodoProcessor())
    
def setup_subscriptions(self):
    self.register_container(TodoContainer())
```

### State Updates

- Always use `store.state.path = value` for updates
- State changes automatically trigger subscriber notifications
- Use `store.get_current_state()` for read-only access
- Built-in Undo/Redo via `store.undo()` and `store.redo()`

### Storybook Development

The Storybook system (`src/pubsubtk/storybook/`) provides component development environment:

- Auto-discovers components marked with `@story` decorator
- Interactive component preview with property manipulation
- Isolated component testing without full application

## File Organization

```
src/pubsubtk/
├── app/              # Application base classes
├── core/             # Core pub/sub and topic functionality  
├── processor/        # Business logic layer
├── store/            # State management
├── storybook/        # Component development environment
├── topic/            # Built-in topics and topic utilities
├── ui/               # UI component base classes and types
└── utils/            # Async utilities and helpers
```

## Development Guidelines

### Component Development

- Use type hints with Pydantic models for state
- Implement proper teardown in `teardown()` method
- Subscribe to specific state paths, not entire state
- Keep Presentational components stateless

### State Design

- Design state as normalized, flat structures when possible
- Use Pydantic models for validation and IDE support
- Avoid deeply nested state mutations
- Group related state in sub-models

### Testing Approach

- Use the sample application (`tests/sample_app/main.py`) as a comprehensive example
- Test components in isolation using Storybook
- Test state logic through direct Store manipulation
- Test pub/sub communication with mock subscribers

## Debugging

The framework includes extensive debug logging:

```python
# Enable debug logging for pub/sub
import logging
logging.basicConfig(level=logging.DEBUG)
```

All pub/sub messages, state changes, and component lifecycle events are logged for debugging.
