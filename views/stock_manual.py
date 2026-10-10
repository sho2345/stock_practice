"""株の基礎知識（docs/stock_manual.md を表示）"""

from pathlib import Path

import streamlit as st

from stock_sim import style, ui

ui.close_dialogs()  # 別のページに移ったら、開いていた売買ダイアログは閉じる
ui.topnav()
style.hero("📗", "株の基礎知識", "株をはじめて学ぶ人向けに、最低限知っておきたいことをまとめました", "small doc")
st.write("")
st.markdown((Path(__file__).resolve().parent.parent / "docs" / "stock_manual.md").read_text(encoding="utf-8"))
