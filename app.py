"""株シミュレータのエントリーポイント。起動: streamlit run app.py"""

import streamlit as st

from stock_sim import style

st.set_page_config(page_title="はじめての株シミュレータ", page_icon="📈", layout="wide")
style.inject_css()

# サイドバーのメニューは使わず、ホーム画面のボタンと各ページ上部のリンクで移動する
nav = st.navigation(
    [
        st.Page("views/home.py", title="ホーム", icon="🏠", default=True),
        st.Page("views/time_machine.py", title="タイムマシンモード", icon="⏳"),
        st.Page("views/realtime.py", title="リアルタイムモード", icon="📡"),
        st.Page("views/app_manual.py", title="アプリの使い方", icon="📘"),
        st.Page("views/stock_manual.py", title="株の基礎知識", icon="📗"),
    ],
    position="hidden",
)
nav.run()
