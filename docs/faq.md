# FAQ

---

**Q. tkinter以外のGUIライブラリで使えますか？**  
A. 現在はTkinter/ttk専用です。PySideやPyQtなどには対応していません。

---

**Q. 状態が複雑化した場合はどうすればよいですか？**  
A. Pydanticモデルを入れ子構造で分割したり、用途ごとにStoreを分割できます。

---

**Q. グローバル状態とローカル状態の使い分けは？**  
A. アプリ全体の状態はStore、Component単位で閉じたローカル状態はコンポーネントの属性や独自Pydanticモデルで管理してください。

---

**Q. 画面遷移やウィンドウ管理はどうやるの？**  
A. `pub_switch_slot()`で画面切り替え、`pub_open_subwindow()`でサブウィンドウ管理ができます。

---

**Q. デバッグ・動作確認のコツは？**  
A. `enable_pubsub_debug_logging()`を使うと、PubSubメッセージの流れをデバッグできます。

---

**Q. Undo/Redoはどう実装しますか？**  
A. PubSubTk v2.0以降では組み込みUndo/Redo機能が利用できます：

```python
# Undo/Redo有効化
self.pub_enable_undo_redo(self.store.state.counter, max_history=50)

# 状態監視
self.sub_undo_status(self.store.state.counter, self.on_undo_status_changed)

# 実行
self.pub_undo(self.store.state.counter)
self.pub_redo(self.store.state.counter)
```

従来の状態全体スナップショット方式も引き続き使用可能ですが、新しい方式の方がメモリ効率が良く推奨されます。詳細は[レシピ集](cookbook.md)を参照してください。

---

**Q. 複数のフィールドで独立したUndo/Redo履歴を持てますか？**  
A. はい、各フィールドごとに独立してUndo/Redo機能を有効化できます：

```python
# テキスト内容は大量履歴
self.pub_enable_undo_redo(self.store.state.text_content, max_history=100)

# フォントサイズは小さい履歴
self.pub_enable_undo_redo(self.store.state.font_size, max_history=20)

# それぞれ独立してUndo/Redo実行
self.pub_undo(self.store.state.text_content)  # テキストのみ戻す
self.pub_undo(self.store.state.font_size)     # フォントサイズのみ戻す
```

---

**Q. Undo/Redo履歴のメモリ使用量を制御したい**  
A. `max_history`パラメータで履歴保持数を調整できます。また、`pub_disable_undo_redo()`で不要になった履歴を完全に削除することも可能です：

```python
# 履歴数を制限
self.pub_enable_undo_redo(self.store.state.data, max_history=10)

# 機能を無効化してメモリ解放
self.pub_disable_undo_redo(self.store.state.data)
```

---

**Q. オートセーブやバックアップはどう実装しますか？**  
A. Pydantic状態の`model_dump()`を活用したファイル保存や、定期的なスナップショット作成で対応できます。詳細は[レシピ集](cookbook.md)を参照してください。

---

**Q. ProcessorやContainerを動的に切り替える方法は？**  
A. `pub_switch_container()`や`pub_register_processor()`を活用してください。

---

**Q. Issue・質問はどこでできますか？**  
A. GitHubの[Issue](https://github.com/vavavavavavavavava/pubsubtk/issues)やDiscussionsでお気軽にどうぞ。

---

他にも質問があれば Issue か PR でお知らせください！
