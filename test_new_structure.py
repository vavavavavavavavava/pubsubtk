#!/usr/bin/env python3
# test_new_structure.py - 新しい構造のインポートテスト

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """新しいディレクトリ構造でのインポートテスト"""
    print("=== 新しいディレクトリ構造インポートテスト ===")
    
    try:
        # メイン公開API
        from pubsubtk.storybook import StorybookApplication, story
        print("✓ メイン公開API: StorybookApplication, story")
        
        # Core モジュール
        from pubsubtk.storybook.core import StoryMeta, StoryContext, StoryRegistry
        print("✓ Core: StoryMeta, StoryContext, StoryRegistry")
        
        # Knobs モジュール
        from pubsubtk.storybook.knobs import KnobSpec, KnobValue, KnobPanel
        print("✓ Knobs: KnobSpec, KnobValue, KnobPanel")
        
        # UI モジュール
        from pubsubtk.storybook.ui import StorybookContainer, StorybookTemplate
        print("✓ UI: StorybookContainer, StorybookTemplate")
        
        # Processors モジュール
        from pubsubtk.storybook.processors import StorybookProcessor
        print("✓ Processors: StorybookProcessor")
        
        print("\n🎉 すべてのインポートが成功しました！")
        return True
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)