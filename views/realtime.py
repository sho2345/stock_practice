"""リアルタイムモード：今日の株価で仮想的に売買し、数か月〜数年かけて結果を見る"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from stock_sim import market_data as md
from stock_sim import storage, style, ui
from stock_sim.portfolio import Portfolio
from stock_sim.stocks import display_name

SAVE_NAME = "realtime"


def sp500_jpy(latest: dict) -> float:
    return latest[md.SP500]["price"] * latest[md.FX]["price"]


def setup(latest: dict) -> None:
    with st.container(key="card_setup"):
        st.markdown("### 🚀 今日から投資を始めよう")
        st.write("今日の実際の株価で株を買い、数日後・数か月後にアプリを開いて結果を確かめます。")
        initial = st.number_input("元手（円）", min_value=100_000, max_value=100_000_000, value=1_000_000, step=100_000)
        st.caption("記録はこのパソコンに保存されます。アプリを開くたびに、その日の株価で資産が計算されます。")
        if st.button(f"{int(initial):,}円 で今日から始める", type="primary", icon="📡", key="rt_start"):
            today = date.today().isoformat()
            pf = Portfolio(initial_cash=float(initial), cash=float(initial))
            storage.save(SAVE_NAME, {
                "start_date": today,
                "portfolio": pf.to_dict(),
                # 指数と比較するため、開始時点の日経平均・S&P500（円換算）を記録しておく
                "bench_start": {"n225": latest[md.N225]["price"], "sp500_jpy": sp500_jpy(latest)},
                "history": [],
            })
            st.rerun()


def apply_splits(pf: Portfolio, today: str) -> list[str]:
    """前回確認した日以降に株式分割があれば株数に反映する。反映した内容のメッセージを返す"""
    messages = []
    for code in list(pf.holdings):
        h = pf.holdings[code]
        try:
            splits = md.fetch_splits(code)
        except Exception:
            continue  # 取得できなければ次回に確認する
        for d, ratio in splits:
            if h.split_checked < d <= today:
                pf.apply_split(code, ratio, d)
                messages.append(f"{display_name(code)} で株式分割（1株→{ratio:g}株）があったため、株数を自動で調整しました。")
        h.split_checked = today
    return messages


def play(latest: dict, state: dict) -> None:
    pf = Portfolio.from_dict(state["portfolio"])
    today = date.today().isoformat()
    for msg in apply_splits(pf, today):
        st.info(msg)

    def current_prices(warn: bool = False) -> dict[str, float]:
        """保有銘柄の最新の円換算価格。売買後は保有銘柄が変わるので都度作り直す"""
        prices = {}
        for code, h in pf.holdings.items():
            p = md.latest_price_jpy(latest, code)
            if p is None:
                if warn:
                    st.warning(f"{display_name(code)} の株価が取得できなかったため、取得単価で仮計算しています。")
                p = h.avg_cost
            prices[code] = p
        return prices

    bs = state["bench_start"]
    initial = pf.initial_cash
    bench = {
        "日経平均": initial * latest[md.N225]["price"] / bs["n225"],
        "S&P500（円換算）": initial * sp500_jpy(latest) / bs["sp500_jpy"],
    }

    def save(p: Portfolio) -> None:
        # 今日の資産額を履歴に記録（同じ日は上書き）してから保存する
        entry = {"date": today, "total": p.total_value(current_prices()), **bench}
        hist = state["history"]
        if hist and hist[-1]["date"] == today:
            hist[-1] = entry
        else:
            hist.append(entry)
        state["portfolio"] = p.to_dict()
        storage.save(SAVE_NAME, state)

    prices = current_prices(warn=True)
    save(pf)

    # ---- 株価の時点と再取得ボタン ----
    jp_date = latest.get("7203.T", {}).get("date", "-")
    us_date = latest.get("AAPL", {}).get("date", "-")
    with st.container(key="card_status"):
        c1, c2 = st.columns([4, 1], vertical_alignment="center")
        c1.markdown(
            f"🗓️ **{state['start_date']}** にスタート　／　📈 株価の時点：日本株 **{jp_date}**・米国株 **{us_date}**  \n"
            "<span style='color:#8a8da3;font-size:.85rem'>取引時間中は約20分遅れの株価、それ以外は直近の終値で売買します（30分ごとに自動更新）</span>",
            unsafe_allow_html=True,
        )
        if c2.button("株価を再取得", icon="🔄", width="stretch"):
            md.fetch_latest_prices.clear()
            st.rerun()

    def native(code: str) -> float | None:
        return latest[code]["price"] if code in latest else None

    def change(code: str) -> float | None:
        info = latest.get(code)
        if not info or not info.get("prev"):
            return None
        return info["price"] / info["prev"] - 1

    one_year_ago = (date.today() - timedelta(days=365)).isoformat()
    mkt = ui.Market(
        key="rt",
        date=today,
        date_format="%Y/%m/%d",
        price=lambda code: md.latest_price_jpy(latest, code),
        native=native,
        fx=latest[md.FX]["price"],
        change=change,
        change_label="前日比",
        history=lambda code, since: md.fetch_daily_history_jpy(code, since),
        chart_history=lambda code: md.fetch_daily_history_jpy(code, one_year_ago),
        chart_title="直近1年の株価（円換算）",
        show_link=True,
        save=save,
    )

    # 資産の推移（v1 で保存した記録は「日経平均なら」などの名前なので、両方に対応する）
    rows = [{
        "date": e["date"],
        "あなたの資産": e["total"],
        "日経平均": e.get("日経平均", e.get("日経平均なら")),
        "S&P500（円換算）": e.get("S&P500（円換算）", e.get("S&P500（円換算）なら")),
    } for e in state["history"]]
    asset_hist = pd.DataFrame(rows).set_index("date")

    ui.dashboard(pf, mkt, prices, bench, asset_hist)
    st.divider()
    ui.reset_button("最初からやり直す", lambda: storage.delete(SAVE_NAME))


ui.topnav()
style.hero("📡", "リアルタイムモード", "今日の本物の株価で売買。ニュースや決算をもとに判断して、未来の結果を確かめよう", "small rt")
st.write("")
ui.show_flash()

try:
    latest_prices = md.fetch_latest_prices()
except Exception as e:  # ネットワークエラーなど
    latest_prices = None
    st.error(f"株価を取得できませんでした。インターネット接続を確認してください。（{e}）")

if latest_prices is not None:
    if md.FX not in latest_prices or md.N225 not in latest_prices or md.SP500 not in latest_prices:
        st.error("為替・指数のデータが取得できませんでした。時間をおいて再読み込みしてください。")
    else:
        saved = storage.load(SAVE_NAME)
        if saved is None:
            setup(latest_prices)
        else:
            play(latest_prices, saved)
