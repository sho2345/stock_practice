"""アプリの使い方（docs/app_manual.md を表示）"""

from pathlib import Path

import streamlit as st

from stock_sim import style, ui

ui.close_dialogs()  # 別のページに移ったら、開いていた売買ダイアログは閉じる
ui.topnav()
style.hero("📘", "アプリの使い方", "このアプリでできること・遊び方をまとめました", "small doc")
st.write("")
st.markdown((Path(__file__).resolve().parent.parent / "docs" / "app_manual.md").read_text(encoding="utf-8"))
