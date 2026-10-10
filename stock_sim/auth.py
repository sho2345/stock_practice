"""ログイン（Google アカウント）。.streamlit/secrets.toml に [auth] があるときだけ有効になる

[auth] が無いとき（自分の PC でそのまま使うとき）はログインなしの「ローカルモード」で動く。
"""

import streamlit as st

from . import style

LOCAL_USER = "local"  # ローカルモードの利用者 ID


def _has_secret(section: str) -> bool:
    try:
        return section in st.secrets
    except Exception:  # secrets.toml が無いとき
        return False


def auth_enabled() -> bool:
    return _has_secret("auth")


def is_logged_in() -> bool:
    return (not auth_enabled()) or bool(st.user.is_logged_in)


def user_id() -> str:
    """保存データを区別するための利用者 ID。Google の利用者ごとに変わらない番号（sub）を使う"""
    if not auth_enabled():
        return LOCAL_USER
    return f"google:{st.user.sub}"


def user_label() -> str:
    if not auth_enabled():
        return ""
    return st.user.get("name") or st.user.get("email") or "ログイン中"


def login_page() -> None:
    """ログインしていないときに表示する画面"""
    style.hero("📈", "はじめての株シミュレータ", "本物の株価で、お金を使わずに投資を体験しよう。株を知らなくても大丈夫！")
    st.write("")
    with st.container(key="card_login"):
        st.markdown("### 🔐 ログインして始めよう")
        st.write(
            "売買の記録は、あなたのアカウントごとに保存されます。"
            "スマホと PC のどちらからでも、同じ続きを遊べます。"
        )
        if st.button("Google アカウントでログイン", type="primary", icon="🔑"):
            st.login()
        st.caption("ログインに使うのは、名前・メールアドレスなどの基本情報だけです。Google のパスワードがこのアプリに渡ることはありません。")
