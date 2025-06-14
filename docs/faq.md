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

**Q. オートセーブやUndo/Redoはどう実装しますか？**  
A. [レシピ集](cookbook.md)に例があります。状態全体のスナップショットを履歴にして`pub_replace_state()`で復元する方式が簡単です。

---

**Q. ProcessorやContainerを動的に切り替える方法は？**  
A. `pub_switch_container()`や`pub_register_processor()`を活用してください。

---

**Q. Issue・質問はどこでできますか？**  
A. GitHubの[Issue](https://github.com/vavavavavavavavava/pubsubtk/issues)やDiscussionsでお気軽にどうぞ。

---

他にも質問があれば Issue か PR でお知らせください！
