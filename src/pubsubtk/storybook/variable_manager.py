# storybook/variable_manager.py - KnobVariableManager
"""tk.Variable の共有管理システム"""

import tkinter as tk
from typing import Dict, Any, Optional
from pubsubtk.storybook.meta import KnobSpec


class KnobVariableManager:
    """グローバルな tk.Variable 共有管理クラス"""
    
    _instance: Optional['KnobVariableManager'] = None
    
    def __init__(self):
        self._variables: Dict[str, tk.Variable] = {}
        self._specs: Dict[str, KnobSpec] = {}
    
    @classmethod
    def get_instance(cls) -> 'KnobVariableManager':
        """シングルトンインスタンスを取得"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def clear_story_variables(self) -> None:
        """現在のStoryの変数をすべてクリア"""
        self._variables.clear()
        self._specs.clear()
    
    def create_or_get_variable(self, spec: KnobSpec) -> tk.Variable:
        """KnobSpecから tk.Variable を作成または取得"""
        if spec.name in self._variables:
            # 既存の変数を返す
            return self._variables[spec.name]
        
        # 新しい変数を作成
        if spec.type_ is bool:
            var = tk.BooleanVar(value=spec.default)
        elif spec.type_ is int:
            var = tk.IntVar(value=spec.default)
        elif spec.type_ is float:
            var = tk.DoubleVar(value=spec.default)
        else:
            var = tk.StringVar(value=str(spec.default))
        
        self._variables[spec.name] = var
        self._specs[spec.name] = spec
        return var
    
    def get_variable(self, name: str) -> Optional[tk.Variable]:
        """名前で変数を取得"""
        return self._variables.get(name)
    
    def get_all_variables(self) -> Dict[str, tk.Variable]:
        """すべての変数を取得"""
        return self._variables.copy()
    
    def get_all_specs(self) -> Dict[str, KnobSpec]:
        """すべてのKnobSpecを取得"""
        return self._specs.copy()
    
    def set_variable_value(self, name: str, value: Any) -> None:
        """変数の値を設定"""
        if name in self._variables:
            self._variables[name].set(value)


# グローバルインスタンス取得用の便利関数
def get_variable_manager() -> KnobVariableManager:
    """KnobVariableManager のグローバルインスタンスを取得"""
    return KnobVariableManager.get_instance()