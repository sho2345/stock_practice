"""両モードで共通して使う画面（資産の状況・マーケット・売買ダイアログなど）"""

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from . import charts
from .portfolio import Portfolio, TradeError
from .stocks import STOCK_BY_CODE, STOCKS, display_name, yahoo_url
from .style import change_html, esc, kpis, money_change_html


@dataclass
class Market:
    """モードごとに異なる「株価の取り方」をまとめたもの。画面部品はこれを通して株価を参照する"""
    key: str  # ウィジェットの key の接頭辞（"tm" / "rt"）
    date: str  # 売買を記録する日付
    date_format: str  # グラフの日付の書式
    price: Callable[[str], float | None]  # 1株の円換算価格（売買できないときは None）
    native: Callable[[str], float | None]  # 1株の現地通貨の価格
    fx: float  # ドル円レート
    change: Callable[[str], float | None]  # 前の期間からの変化率
    change_label: str  # "前月比" / "前日比"
    history: Callable[[str, str], pd.Series]  # (銘柄, 開始日) → その日から現在までの円換算の株価
    chart_history: Callable[[str], pd.Series]  # 売買画面に表示する株価の推移
    chart_title: str
    show_link: bool  # ニュース（Yahoo!ファイナンス）へのリンクを出すか
    save: Callable[[Portfolio], None]  # 売買後に保存する処理
    # 売買できない銘柄のカードに出す理由（銘柄コード → 文言）
    unavailable: Callable[[str], str] = lambda code: "株価を取得できませんでした"


# ======================= 小さな部品 =======================

def yen(x: float) -> str:
    return f"{x:,.0f}円"


def signed_yen(x: float) -> str:
    return f"{x:+,.0f}円"


def price_text(mkt: Market, code: str) -> tuple[str, str]:
    """株価の表示（メイン, 補足）。米国株はドルと円換算の両方を出す"""
    p, n = mkt.price(code), mkt.native(code)
    if p is None:
        return "－", ""
    if STOCK_BY_CODE[code].market == "US":
        return f"${n:,.2f}", f"約{p:,.0f}円（1ドル＝{mkt.fx:,.1f}円）"
    return yen(p), ""


def badges_html(code: str, owned: int = 0) -> str:
    cat = STOCK_BY_CODE[code].category
    cls = {"日本株": "jp", "米国株": "us", "ETF": "etf"}[cat]
    html = f'<span class="badge {cls}">{cat}</span>'
    if owned:
        html += f'<span class="badge own">保有中 {owned:,}株</span>'
    return f'<div class="badges">{html}</div>'


def _css_key(code: str) -> str:
    return code.replace(".", "_").replace("^", "")


def show_flash() -> None:
    """再読み込み後に、直前の操作結果メッセージを表示する"""
    msg = st.session_state.pop("flash", None)
    if msg:
        st.toast(msg, icon="✅")
        st.success(msg)


def topnav() -> None:
    """各ページ上部のナビゲーション"""
    with st.container(horizontal=True, key="topnav", vertical_alignment="center", gap="medium"):
        st.page_link("views/home.py", label="ホーム", icon="🏠")
        st.page_link("views/app_manual.py", label="アプリの使い方", icon="📘")
        st.page_link("views/stock_manual.py", label="株の基礎知識", icon="📗")


def color_map(pf: Portfolio) -> dict[str, str]:
    """保有銘柄ごとの色（買った順に固定の8色。9銘柄目以降はグレー）"""
    return {code: (charts.PALETTE[i] if i < len(charts.PALETTE) else charts.OTHER)
            for i, code in enumerate(pf.holdings)}


def holding_since(pf: Portfolio, code: str) -> str | None:
    """今持っている株を買い始めた日（一度すべて売った場合は、その後に買い直した日）"""
    since, shares = None, 0
    for t in pf.trades:
        if t["code"] != code:
            continue
        if t["side"] == "買い":
            if shares == 0:
                since = t["date"]
            shares += t["shares"]
        else:  # 売りはマイナス、株式分割はプラス
            shares += -t["shares"] if t["side"] == "売り" else t["shares"]
    return since if shares > 0 else None


def _safe_history(mkt: Market, code: str, since: str) -> pd.Series:
    try:
        return mkt.history(code, since)
    except Exception:  # ネットワークエラーなどでグラフが出せなくても画面全体は止めない
        return pd.Series(dtype=float)


# ======================= 資産のまとめ =======================

def summary(pf: Portfolio, prices: dict[str, float], bench: dict[str, float]) -> None:
    total = pf.total_value(prices)
    stock_value = pf.market_value(prices)
    profit = total - pf.initial_cash
    unrealized = stock_value - sum(h.cost for h in pf.holdings.values())
    ratio = profit / pf.initial_cash
    kpis([
        {"label": "総資産（現金＋株）", "value": yen(total), "main": True,
         "sub": f"元手 {yen(pf.initial_cash)} から {money_change_html(profit, ratio, color=False)}"},
        {"label": "合計の損益", "value": money_change_html(profit),
         "sub": f"含み損益 {money_change_html(unrealized)}<br>確定損益 {money_change_html(pf.realized)}"},
        {"label": "株の評価額", "value": yen(stock_value), "sub": f"{len(pf.holdings)} 銘柄を保有中"},
        {"label": "現金", "value": yen(pf.cash), "sub": f"総資産の {pf.cash / total * 100:.0f}%" if total else ""},
    ])
    # 成績くらべ：同じ元手で最初に指数へ全額投資していた場合
    items = [f'<span class="vs-item">🙋 あなた {change_html(ratio)}</span>']
    wins = losses = 0
    for label, v in bench.items():
        r = v / pf.initial_cash - 1
        diff = round((ratio - r) * 1000)  # 0.1% 未満の差は「同じ」とみなす（小数の誤差対策）
        wins += diff > 0
        losses += diff < 0
        items.append(f'<span class="vs-item">{esc(label)} {change_html(r)}</span>')
    if wins == losses == 0:
        verdict = "⚖️ 指数とほぼ同じ成績です"
    elif losses == 0:
        verdict = "🏆 指数に勝っています！"
    elif wins == 0:
        verdict = "📉 今のところ指数に負けています"
    else:
        verdict = "⚖️ 片方の指数には勝っています"
    st.markdown(
        f'<div class="versus"><b>成績くらべ</b><span style="color:#8a8da3;font-size:.8rem">'
        f'（同じ元手で最初に全額投資した場合）</span>{"".join(items)}<span class="verdict">{verdict}</span></div>',
        unsafe_allow_html=True,
    )


# ======================= メイン画面（3つのタブ） =======================

def dashboard(pf: Portfolio, mkt: Market, prices: dict[str, float], bench: dict[str, float],
              asset_hist: pd.DataFrame) -> None:
    summary(pf, prices, bench)
    st.write("")
    tab_pf, tab_market, tab_log = st.tabs(
        ["📊 ポートフォリオ（持っている株）", "🛒 株を買う・売る", f"📜 取引履歴（{len(pf.trades)}）"],
        key=f"{mkt.key}_tabs",
    )
    with tab_pf:
        _portfolio_tab(pf, mkt, prices, asset_hist)
    with tab_market:
        _market_tab(pf, mkt)
    with tab_log:
        _history_tab(pf)
    # 売買ダイアログは「開いている銘柄」を記録しておき、再読み込みされても開いたままにする
    code = st.session_state.get(f"{mkt.key}_dialog")
    if code in STOCK_BY_CODE:
        _trade_dialog(code, pf, mkt)


def _portfolio_tab(pf: Portfolio, mkt: Market, prices: dict[str, float], asset_hist: pd.DataFrame) -> None:
    st.markdown("#### 資産の推移")
    if len(asset_hist) >= 2:
        st.caption("実線：あなたの資産　／　破線：同じ元手を最初に日経平均・S&P500 に全額投資していた場合")
        st.altair_chart(charts.asset_chart(asset_hist, mkt.date_format), width="stretch")
    else:
        st.caption("時間が進むと（リアルタイムモードでは別の日にアプリを開くと）ここに資産の推移グラフが表示されます。")

    if not pf.holdings:
        st.info("まだ株を持っていません。上の「🛒 株を買う・売る」タブから、気になる銘柄を買ってみましょう！")
        return

    colors = color_map(pf)
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown("#### 資産の内訳")
        items = [("現金", pf.cash, charts.CASH)]
        other = 0.0
        for code, h in pf.holdings.items():
            if colors[code] == charts.OTHER:
                other += h.shares * prices[code]
            else:
                items.append((STOCK_BY_CODE[code].short_name, h.shares * prices[code], colors[code]))
        if other:
            items.append(("その他の銘柄", other, charts.OTHER))
        st.altair_chart(charts.allocation_donut(items), width="stretch")
    with right:
        st.markdown("#### 銘柄ごとの値動き")
        st.caption("買い始めた時点を 0% として、それぞれの株価が何%上がった（下がった）かを比べます")
        series, cmap = {}, {}
        for code in pf.holdings:
            if colors[code] == charts.OTHER:
                continue
            since = holding_since(pf, code) or mkt.date
            s = _safe_history(mkt, code, since)
            if len(s) >= 2:
                name = STOCK_BY_CODE[code].short_name
                series[name], cmap[name] = s, colors[code]
        if series:
            st.altair_chart(charts.performance_chart(series, cmap, mkt.date_format), width="stretch")
        else:
            st.caption("買ってから時間が経つと、銘柄ごとの値動きを比べるグラフが表示されます。")
        if len(pf.holdings) > len(charts.PALETTE):
            st.caption(f"※ グラフに表示するのは最初に買った {len(charts.PALETTE)} 銘柄までです。")

    st.markdown("#### 持っている株")
    codes = list(pf.holdings)
    for i in range(0, len(codes), 3):
        cols = st.columns(3)
        for col, code in zip(cols, codes[i:i + 3]):
            with col:
                _holding_card(pf, mkt, code, prices[code], colors[code])


def _holding_card(pf: Portfolio, mkt: Market, code: str, price: float, color: str) -> None:
    h = pf.holdings[code]
    s = STOCK_BY_CODE[code]
    value = h.shares * price
    pl = value - h.cost
    main, sub = price_text(mkt, code)
    with st.container(key=f"card_h_{mkt.key}_{_css_key(code)}"):
        st.markdown(
            f'{badges_html(code)}'
            f'<div class="stock-name"><span style="color:{color}">●</span> {esc(s.short_name)}</div>'
            f'<div class="stock-code">{esc(code.removesuffix(".T"))}　{h.shares:,}株・平均取得単価 {yen(h.avg_cost)}</div>'
            f'<div style="margin-top:8px" class="stock-sub">評価額</div>'
            f'<div class="stock-price">{yen(value)}</div>'
            f'<div>{money_change_html(pl, pl / h.cost if h.cost else None)}</div>'
            f'<div class="stock-sub">現在の株価 {main} {sub}</div>',
            unsafe_allow_html=True,
        )
        hist = _safe_history(mkt, code, holding_since(pf, code) or mkt.date)
        if len(hist) >= 2:
            st.altair_chart(charts.sparkline(hist, color), width="stretch")
        st.button("売買する", key=f"{mkt.key}_hbtn_{code}", width="stretch",
                  on_click=_open_dialog, args=(mkt.key, code))


def _market_tab(pf: Portfolio, mkt: Market) -> None:
    st.markdown("気になる銘柄の **「詳しく見る・売買」** を押すと、株価のグラフを見て売買できます。いくつの銘柄でも買えます。")
    cat = st.segmented_control(
        "表示する銘柄", ["すべて", "日本株", "米国株", "ETF"], default="すべて",
        key=f"{mkt.key}_filter", required=True, label_visibility="collapsed",
    )
    codes = [s.code for s in STOCKS if cat == "すべて" or s.category == cat]
    for i in range(0, len(codes), 3):
        cols = st.columns(3)
        for col, code in zip(cols, codes[i:i + 3]):
            with col:
                _stock_card(pf, mkt, code)


def _stock_card(pf: Portfolio, mkt: Market, code: str) -> None:
    s = STOCK_BY_CODE[code]
    owned = pf.holdings[code].shares if code in pf.holdings else 0
    with st.container(key=f"card_m_{mkt.key}_{_css_key(code)}"):
        if mkt.price(code) is None:
            price_html = f'<div class="stock-price" style="color:#8a8da3;font-size:1rem">{mkt.unavailable(code)}</div>'
        else:
            main, sub = price_text(mkt, code)
            price_html = (f'<div class="stock-price">{main}</div>'
                          f'<div class="stock-sub">{mkt.change_label} {change_html(mkt.change(code))}　{sub}</div>')
        st.markdown(
            f'{badges_html(code, owned)}<div class="stock-name">{esc(s.name)}</div>'
            f'<div class="stock-code">{esc(code.removesuffix(".T"))}</div>'
            f'<div class="stock-desc">{esc(s.description)}</div>{price_html}',
            unsafe_allow_html=True,
        )
        st.button("詳しく見る・売買", key=f"{mkt.key}_mbtn_{code}", width="stretch",
                  type="primary" if owned else "secondary", on_click=_open_dialog, args=(mkt.key, code))


def _open_dialog(mode_key: str, code: str) -> None:
    st.session_state[f"{mode_key}_dialog"] = code


def close_dialogs() -> None:
    """売買ダイアログを閉じた状態にする（× で閉じたとき・売買が終わったとき・時間を進めたとき）"""
    for k in ("tm_dialog", "rt_dialog"):
        st.session_state.pop(k, None)


@st.dialog("銘柄の詳細と売買", width="large", on_dismiss=close_dialogs)
def _trade_dialog(code: str, pf: Portfolio, mkt: Market) -> None:
    s = STOCK_BY_CODE[code]
    owned = pf.holdings[code].shares if code in pf.holdings else 0
    st.markdown(
        f'{badges_html(code, owned)}<div class="stock-name" style="font-size:1.4rem">{esc(s.name)}'
        f' <span class="stock-code">{esc(code.removesuffix(".T"))}</span></div>'
        f'<div class="stock-sub" style="font-size:.95rem;margin-bottom:6px">{esc(s.description)}</div>',
        unsafe_allow_html=True,
    )
    if mkt.show_link:
        st.link_button("📰 この会社のニュース・業績を見る（Yahoo!ファイナンス）", yahoo_url(code))

    price = mkt.price(code)
    if price is None:
        st.warning(f"{mkt.unavailable(code)}。そのため売買できません。")
        return

    try:
        hist = mkt.chart_history(code)
    except Exception:
        hist = pd.Series(dtype=float)
    if len(hist) >= 2:
        color = color_map(pf).get(code, charts.PALETTE[0])
        st.markdown(f"**{mkt.chart_title}**")
        st.altair_chart(charts.price_chart(hist, color, mkt.date_format), width="stretch")

    main, sub = price_text(mkt, code)
    c1, c2 = st.columns(2)
    c1.markdown(
        f'<div class="kpi"><div class="label">現在の株価</div><div class="value">{main}</div>'
        f'<div class="sub">{sub} {mkt.change_label} {change_html(mkt.change(code))}</div></div>',
        unsafe_allow_html=True,
    )
    if owned:
        h = pf.holdings[code]
        pl = owned * price - h.cost
        own_sub = f"平均取得単価 {yen(h.avg_cost)}<br>損益 {money_change_html(pl, pl / h.cost)}"
    else:
        own_sub = "まだ持っていません"
    c2.markdown(
        f'<div class="kpi"><div class="label">保有株数</div><div class="value">{owned:,}株</div>'
        f'<div class="sub">{own_sub}</div></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    side = st.segmented_control("注文の種類", ["買う", "売る"], default="買う", key=f"{mkt.key}_side", required=True)
    max_shares = int(pf.cash // price) if side == "買う" else owned
    hint = f"今の現金（{yen(pf.cash)}）で最大 {max_shares:,} 株買えます" if side == "買う" else f"最大 {owned:,} 株売れます"
    shares = int(st.number_input("株数", min_value=1, value=1, step=1, key=f"{mkt.key}_shares", help=hint))
    st.caption(hint)
    amount = shares * price
    after = pf.cash - amount if side == "買う" else pf.cash + amount
    st.markdown(f"概算金額：**{yen(amount)}**　→　注文後の現金：**{yen(after)}**")

    if st.button(f"{shares:,} 株を{side}", type="primary", width="stretch", key=f"{mkt.key}_submit"):
        try:
            if side == "買う":
                pf.buy(code, shares, price, mkt.date, mkt.native(code))
                msg = f"{s.short_name} を {shares:,} 株買いました（{yen(amount)}）"
            else:
                profit = pf.sell(code, shares, price, mkt.date, mkt.native(code))
                msg = f"{s.short_name} を {shares:,} 株売りました（{yen(amount)}、確定損益 {signed_yen(profit)}）"
        except TradeError as e:
            st.error(str(e))
            return
        mkt.save(pf)
        st.session_state["flash"] = msg
        close_dialogs()
        st.rerun()


def _history_tab(pf: Portfolio) -> None:
    if not pf.trades:
        st.info("まだ取引はありません。")
        return
    st.markdown(f"売却して確定した損益の合計：{money_change_html(pf.realized)}", unsafe_allow_html=True)
    rows = []
    for t in reversed(pf.trades):
        rows.append({
            "日付": t["date"],
            "種類": t["side"],
            "銘柄": display_name(t["code"]),
            "株数": f"{t['shares']:,}",
            "単価（円換算）": yen(t["price"]) if t.get("price") is not None else "-",
            "金額": yen(t["amount"]) if t.get("amount") else "-",
            "確定損益": signed_yen(t["profit"]) if t.get("profit") is not None else (t.get("note") or "-"),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def reset_button(label: str, on_reset: Callable[[], None]) -> None:
    """誤操作を防ぐため、確認を 1 回はさんでから最初からやり直す"""
    with st.popover(label, icon="🔄"):
        st.write("今の資産と取引履歴はすべて消えます。よろしいですか？")
        if st.button("はい、最初からやり直す", type="primary"):
            on_reset()
            st.rerun()
