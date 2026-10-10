"""ホーム画面：タイトルとモード選択。マニュアルへのボタンは左下に置く"""

import streamlit as st

from stock_sim import auth, storage, style, ui

ui.close_dialogs()  # 別のページに移ったら、開いていた売買ダイアログは閉じる
if auth.auth_enabled():
    with st.container(horizontal=True, horizontal_alignment="right"):
        ui.user_menu()
style.hero("📈", "はじめての株シミュレータ", "本物の株価で、お金を使わずに投資を体験しよう。株を知らなくても大丈夫！")

st.markdown(
    """
<div class="steps">
  <div class="step"><span class="num">1</span><b>元手を受け取る</b><div>最初に仮想のお金（100万円など）を受け取ります。</div></div>
  <div class="step"><span class="num">2</span><b>株を選んで買う</b><div>日本・米国の有名企業など50銘柄から、いくつでも買えます。</div></div>
  <div class="step"><span class="num">3</span><b>時間がたつと…</b><div>実際の値動きで資産が増えたり減ったり。合計の収支を確かめよう。</div></div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("### 🎮 モードを選んでスタート")


def mode_card(key: str, emoji: str, title: str, desc: str, points: list[str], status: str | None, page: str) -> None:
    with st.container(key=f"mode_{key}"):
        items = "".join(f"<li>{p}</li>" for p in points)
        st.markdown(
            f'<div class="mode-emoji">{emoji}</div><div class="mode-title">{title}</div>'
            f'<div class="mode-desc">{desc}</div><ul class="mode-points">{items}</ul>'
            + (f'<div class="continue">▶ {status}</div>' if status else ""),
            unsafe_allow_html=True,
        )
        if st.button("続きから遊ぶ" if status else "このモードで遊ぶ", key=f"go_{key}", type="primary",
                     width="stretch", icon="➡️"):
            st.switch_page(page)


# 保存データがあれば「続きから」の情報を出す
tm = storage.load("time_machine")
tm_status = None
if tm:
    y, m = tm["current"].split("-")
    tm_status = f"続きから：いまは {y}年{int(m)}月・総資産 {ui.yen(tm['history'][-1]['total'])}"
rt = storage.load("realtime")
rt_status = None
if rt:
    rt_status = f"続きから：{rt['start_date']} にスタート"
    if rt["history"]:
        rt_status += f"・前回の総資産 {ui.yen(rt['history'][-1]['total'])}"

c1, c2 = st.columns(2, gap="large")
with c1:
    mode_card(
        "tm", "⏳", "タイムマシンモード",
        "過去の好きな時点（2005年〜）にタイムスリップ。ボタンで時間を早送りしながら投資します。",
        ["数年分の値動きを数分で体験", "リーマン・ショックやコロナ・ショックも体験できる", "まずはここから始めるのがおすすめ"],
        tm_status, "views/time_machine.py",
    )
with c2:
    mode_card(
        "rt", "📡", "リアルタイムモード",
        "今日の本物の株価で売買。数日後・数か月後にアプリを開いて結果を確かめます。",
        ["ニュースや決算を見て判断する練習に", "現実と同じ時間の流れで投資を体験", "未来は誰にも分からない、本番さながらの練習"],
        rt_status, "views/realtime.py",
    )

# ---- 左下：マニュアル ----
st.write("")
st.write("")
st.markdown("##### 📚 はじめての方へ")
with st.container(horizontal=True, gap="small"):
    if st.button("アプリの使い方", icon="📘"):
        st.switch_page("views/app_manual.py")
    if st.button("株の基礎知識", icon="📗"):
        st.switch_page("views/stock_manual.py")
    st.page_link("views/privacy.py", label="プライバシーポリシー", icon="🔒")
st.markdown(
    '<div class="footer-note">※ このアプリは学習用のシミュレータです。特定の銘柄の売買をすすめるものではありません。</div>',
    unsafe_allow_html=True,
)
