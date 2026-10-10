"""タイムマシンモード：過去の好きな時点から、実際の株価で月単位にシミュレーションする"""

import pandas as pd
import streamlit as st

from stock_sim import market_data as md
from stock_sim import storage, style, ui
from stock_sim.portfolio import Portfolio

SAVE_NAME = "time_machine"
STEPS = {"▶ 1か月": 1, "▶▶ 3か月": 3, "⏩ 半年": 6, "🚀 1年": 12}


def fmt_month(m: str) -> str:
    y, mo = m.split("-")
    return f"{y}年{int(mo)}月"


def benchmarks(df: pd.DataFrame, start: str, month: str, initial: float) -> dict[str, float]:
    """元手を最初に全額、日経平均・S&P500（円換算）に投資していた場合の金額"""
    n225 = initial * df.at[month, md.N225] / df.at[start, md.N225]
    sp_now = df.at[month, md.SP500] * df.at[month, md.FX]
    sp_start = df.at[start, md.SP500] * df.at[start, md.FX]
    return {"日経平均": n225, "S&P500（円換算）": initial * sp_now / sp_start}


def fetch_button(label: str, key: str) -> None:
    if st.button(label, type="primary", icon="⬇️", key=key):
        with st.spinner("株価データを取得しています…"):
            try:
                failed = md.fetch_monthly_prices()
            except Exception as e:  # ネットワークエラーなど
                st.error(f"取得に失敗しました：{e}")
                return
        msg = "株価データを取得しました。"
        if failed:
            msg += f"（取得できなかった銘柄：{', '.join(failed)}）"
        st.session_state["flash"] = msg
        st.rerun()


def setup(df: pd.DataFrame) -> None:
    months = list(df.index)
    with st.container(key="card_setup"):
        st.markdown("### 🧭 いつにタイムスリップしますか？")
        st.caption(
            "おすすめ：2008年1月（リーマン・ショック直前）や 2020年1月（コロナ・ショック直前）など、"
            "大きな出来事の前から始めると、株価の激しい動きを体験できます。"
        )
        # 少なくとも1か月は進められるよう、最後の月は開始月に選べない
        selectable = months[:-1]
        years = sorted({m[:4] for m in selectable})
        c1, c2, c3 = st.columns(3)
        year = c1.selectbox("開始する年", years, index=years.index("2015") if "2015" in years else 0)
        month_opts = [m for m in selectable if m.startswith(year)]
        # 年を変えたら月の選択をリセットするため、key に年を含める
        start = c2.selectbox("開始する月", month_opts, format_func=lambda m: f"{int(m[5:])}月", key=f"tm_month_{year}")
        initial = c3.number_input("元手（円）", min_value=100_000, max_value=100_000_000, value=1_000_000, step=100_000)
        st.caption(f"データの範囲：{fmt_month(months[0])} 〜 {fmt_month(months[-1])}")
        if st.button(f"{fmt_month(start)} から {int(initial):,}円 で始める", type="primary", icon="⏳", key="tm_start"):
            pf = Portfolio(initial_cash=float(initial), cash=float(initial))
            storage.save(SAVE_NAME, {
                "start": start,
                "current": start,
                "portfolio": pf.to_dict(),
                "history": [{"month": start, "total": float(initial)}],
            })
            st.rerun()

    with st.expander("株価データを最新にする"):
        st.write("先月までの最新データを取り直します（新しい月のデータを追加したいとき用）。")
        fetch_button("株価データを更新する", key="tm_fetch_update")


def time_panel(months: list[str], start: str, cur: str, on_advance) -> None:
    """現在の日付・経過・時間を進めるボタンをまとめた操作パネル"""
    idx, s_idx = months.index(cur), months.index(start)
    is_end = idx == len(months) - 1
    elapsed = idx - s_idx
    progress = elapsed / max(len(months) - 1 - s_idx, 1)
    with st.container(key="tm_panel"):
        left, right = st.columns([3, 2], vertical_alignment="center", gap="large")
        left.markdown(
            f'<div class="tm-now-label">NOW ─ いまは</div><div class="tm-now">📅 {fmt_month(cur)}</div>'
            f'<div class="tm-range">{fmt_month(start)} に出発して {elapsed // 12}年{elapsed % 12}か月経過'
            f'　／　ゴール：{fmt_month(months[-1])}</div>'
            f'<div class="tm-bar"><div style="width:{progress * 100:.1f}%"></div></div>',
            unsafe_allow_html=True,
        )
        with right:
            right.markdown('<div class="tm-now-label">時間を進める</div>', unsafe_allow_html=True)
            labels = list(STEPS.items())
            for row in (labels[:2], labels[2:]):
                cols = st.columns(2)
                for col, (label, n) in zip(cols, row):
                    if col.button(label, disabled=is_end, width="stretch", key=f"tm_step_{n}"):
                        on_advance(n)


def play(df: pd.DataFrame, state: dict) -> None:
    months = list(df.index)
    pf = Portfolio.from_dict(state["portfolio"])
    start, cur = state["start"], state["current"]
    if cur not in months:
        st.error("保存データの月が株価データに見つかりません。最初からやり直してください。")
        ui.reset_button("最初からやり直す", lambda: storage.delete(SAVE_NAME))
        return
    idx = months.index(cur)

    def prices_at(month: str) -> dict[str, float]:
        return {code: md.monthly_price_jpy(df, code, month) for code in pf.holdings}

    def save(p: Portfolio) -> None:
        state["portfolio"] = p.to_dict()
        storage.save(SAVE_NAME, state)

    def advance(n: int) -> None:
        for m in months[idx + 1: min(idx + n, len(months) - 1) + 1]:
            state["history"].append({"month": m, "total": pf.total_value(prices_at(m))})
            state["current"] = m
        save(pf)
        if state["current"] == months[-1]:
            st.session_state["tm_finished"] = True
        ui.close_dialogs()
        st.rerun()

    time_panel(months, start, cur, advance)

    prices = prices_at(cur)
    if idx == len(months) - 1:
        if st.session_state.pop("tm_finished", False):
            st.balloons()
        total = pf.total_value(prices)
        st.success(
            f"🏁 ゴール（{fmt_month(cur)}）に到着しました！ {fmt_month(start)} に {ui.yen(pf.initial_cash)} で始めて、"
            f"最終的な資産は **{ui.yen(total)}**（{ui.signed_yen(total - pf.initial_cash)}）でした。"
        )

    def native(code: str) -> float | None:
        v = df.at[cur, code]
        return None if pd.isna(v) else float(v)

    def change(code: str) -> float | None:
        if idx == 0:
            return None
        before, now = df.at[months[idx - 1], code], df.at[cur, code]
        return None if pd.isna(before) or pd.isna(now) else float(now / before - 1)

    mkt = ui.Market(
        key="tm",
        date=cur,
        date_format="%Y/%m",
        price=lambda code: md.monthly_price_jpy(df, code, cur),
        native=native,
        fx=float(df.at[cur, md.FX]),
        change=change,
        change_label="前月比",
        history=lambda code, since: md.monthly_series_jpy(df, code, cur).loc[since:],
        chart_history=lambda code: md.monthly_series_jpy(df, code, cur),
        chart_title=f"株価の推移（円換算・{fmt_month(cur)}まで。未来はまだ見えません）",
        show_link=False,
        save=save,
        unavailable=lambda code: "株価データが未取得です（上の「更新する」を押してください）"
        if code not in df.columns else "この時点ではまだ上場していません",
    )

    # 資産の推移（自分 vs 指数に全額投資した場合）
    hist = pd.DataFrame(state["history"]).set_index("month")
    asset_hist = pd.DataFrame({"あなたの資産": hist["total"]})
    for m in hist.index:
        for label, v in benchmarks(df, start, m, pf.initial_cash).items():
            asset_hist.at[m, label] = v

    ui.dashboard(pf, mkt, prices, benchmarks(df, start, cur, pf.initial_cash), asset_hist)
    st.divider()
    ui.reset_button("最初からやり直す", lambda: storage.delete(SAVE_NAME))


ui.topnav()
style.hero("⏳", "タイムマシンモード", "過去にタイムスリップして、実際の株価の動きで投資を体験しよう", "small tm")
st.write("")
ui.show_flash()

prices_df = md.load_monthly_prices()
# データが無い（初回・クラウドの再起動後）か、追加した銘柄のデータが無いときは自動で取得する。
# 失敗したときに何度も取りに行かないよう、自動取得は 1 回のセッションにつき 1 回まで
if (prices_df is None or md.missing_codes(prices_df)) and not st.session_state.get("tm_auto_fetched"):
    st.session_state["tm_auto_fetched"] = True
    with st.spinner("株価データを準備しています（初回は数十秒かかります）…"):
        try:
            md.fetch_monthly_prices()
        except Exception as e:  # ネットワークエラーなど
            st.error(f"株価データを取得できませんでした：{e}")
    prices_df = md.load_monthly_prices()

if prices_df is None:
    with st.container(key="card_download"):
        st.markdown("### 株価データを取得できませんでした")
        st.write("インターネット接続を確認して、もう一度お試しください。")
        fetch_button("株価データをダウンロードする", key="tm_fetch_first")
else:
    missing = md.missing_codes(prices_df)
    if missing:
        with st.container(key="card_missing"):
            st.warning(f"{len(missing)} 銘柄の株価データがまだありません。更新すると売買できるようになります（数十秒かかります）。")
            fetch_button("株価データを更新する", key="tm_fetch_missing")
    saved = storage.load(SAVE_NAME)
    if saved is None:
        setup(prices_df)
    else:
        play(prices_df, saved)
