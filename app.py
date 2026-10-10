"""株シミュレータのエントリーポイント。起動: streamlit run app.py"""

import streamlit as st

from stock_sim import auth, style

st.set_page_config(page_title="はじめての株シミュレータ", page_icon="📈", layout="wide")
style.inject_css()

# プライバシーポリシーは、Google のログイン設定で公開 URL（/privacy）として使うため、ログイン前でも見られるようにする
privacy = st.Page("views/privacy.py", title="プライバシーポリシー", icon="🔒", url_path="privacy")

# ログインが有効なとき（secrets.toml に [auth] があるとき）は、ログインするまでログイン画面とポリシーだけを出す
if not auth.is_logged_in():
    pages = [st.Page(auth.login_page, title="ログイン", icon="🔑", default=True), privacy]
else:
    # サイドバーのメニューは使わず、ホーム画面のボタンと各ページ上部のリンクで移動する
    pages = [
        st.Page("views/home.py", title="ホーム", icon="🏠", default=True),
        st.Page("views/time_machine.py", title="タイムマシンモード", icon="⏳"),
        st.Page("views/realtime.py", title="リアルタイムモード", icon="📡"),
        st.Page("views/app_manual.py", title="アプリの使い方", icon="📘"),
        st.Page("views/stock_manual.py", title="株の基礎知識", icon="📗"),
        privacy,
    ]
st.navigation(pages, position="hidden").run()
