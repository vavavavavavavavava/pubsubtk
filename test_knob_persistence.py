#!/usr/bin/env python3
# test_knob_persistence.py - Knob値永続化のテスト
"""Knob値の永続化機能をテストする簡単なスクリプト"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pubsubtk.storybook.knob_store import get_knob_store
from pubsubtk.storybook.knob.knob_types import KnobSpec, KnobValue
from pubsubtk.storybook.context import StoryContext

# テスト用の親ウィジェット（ダミー）
class DummyWidget:
    pass

def test_knob_persistence():
    """Knob値永続化のテスト"""
    print("=== Knob値永続化テスト ===")
    
    # ストアをクリア
    store = get_knob_store()
    store.clear_story("test_story")
    
    # 1回目: 初期値でknobを作成
    print("\n1. 初回作成（デフォルト値）:")
    ctx1 = StoryContext(parent=DummyWidget())
    ctx1.set_story_id("test_story")
    
    text_knob = ctx1.knob("text", str, "Hello", desc="テキスト")
    number_knob = ctx1.knob("number", int, 42, desc="数値", range_=(0, 100))
    bool_knob = ctx1.knob("enabled", bool, True, desc="有効")
    
    print(f"text: {text_knob.value}")
    print(f"number: {number_knob.value}")
    print(f"enabled: {bool_knob.value}")
    
    # 値を変更
    print("\n2. 値を変更:")
    text_knob.value = "Changed Text"
    number_knob.value = 75
    bool_knob.value = False
    
    print(f"text: {text_knob.value}")
    print(f"number: {number_knob.value}")
    print(f"enabled: {bool_knob.value}")
    
    # 2回目: 新しいコンテキストで同じstory_idを使用
    print("\n3. 新しいコンテキストで復元:")
    ctx2 = StoryContext(parent=DummyWidget())
    ctx2.set_story_id("test_story")
    
    text_knob2 = ctx2.knob("text", str, "Hello", desc="テキスト")
    number_knob2 = ctx2.knob("number", int, 42, desc="数値", range_=(0, 100))
    bool_knob2 = ctx2.knob("enabled", bool, True, desc="有効")
    
    print(f"text: {text_knob2.value}")
    print(f"number: {number_knob2.value}")
    print(f"enabled: {bool_knob2.value}")
    
    # 検証
    success = (
        text_knob2.value == "Changed Text" and
        number_knob2.value == 75 and
        bool_knob2.value == False
    )
    
    print(f"\n=== 結果: {'成功' if success else '失敗'} ===")
    if success:
        print("値が正しく永続化されています")
    else:
        print("値の永続化に失敗しています")
    
    return success

if __name__ == "__main__":
    test_knob_persistence()