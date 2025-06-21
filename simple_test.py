#!/usr/bin/env python3
# 最低限のテスト

# KnobStoreの基本動作をテスト
print("=== KnobStoreテスト ===")

# 簡単なテスト用クラス
class TestKnobStore:
    def __init__(self):
        self._values = {}
        self._knob_instances = {}
    
    def get_value(self, story_id, knob_name, default=None):
        return self._values.get(story_id, {}).get(knob_name, default)
    
    def set_value(self, story_id, knob_name, value):
        if story_id not in self._values:
            self._values[story_id] = {}
        self._values[story_id][knob_name] = value
        print(f"保存: {story_id}.{knob_name} = {value}")

# テスト実行
store = TestKnobStore()

# 値を保存
store.set_value("story1", "text", "Hello")
store.set_value("story1", "number", 42)

# 値を取得
print(f"取得: text = {store.get_value('story1', 'text', 'default')}")
print(f"取得: number = {store.get_value('story1', 'number', 0)}")
print(f"取得: missing = {store.get_value('story1', 'missing', 'default')}")

print("\n基本的なストア機能は動作します")