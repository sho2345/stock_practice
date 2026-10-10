"""プライバシーポリシー（docs/privacy.md を表示）。Google のログイン設定で公開 URL として使うため、ログイン前でも見られる"""

from pathlib import Path

import streamlit as st

from stock_sim import auth, style, ui

if auth.is_logged_in():
    ui.close_dialogs()  # 別のページに移ったら、開いていた売買ダイアログは閉じる
    ui.topnav()
style.hero("🔒", "プライバシーポリシー", "このアプリで扱う情報と、その使い方について", "small doc")
st.write("")
st.markdown((Path(__file__).resolve().parent.parent / "docs" / "privacy.md").read_text(encoding="utf-8"))

if not auth.is_logged_in():
    if st.button("Google アカウントでログイン", type="primary", icon="🔑"):
        st.login()
