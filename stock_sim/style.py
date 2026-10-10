"""見た目（CSS）と、カードなどの HTML 部品"""

import html

import streamlit as st

# 値上がり・値下がりの色（色だけに頼らず ▲▼ の記号も必ず付ける）
UP = "#0b7d3e"
DOWN = "#c43535"

CSS = """
<style>
/* ---- 全体 ---- */
.block-container { padding-top: 2.2rem; max-width: 1180px; }
h1, h2, h3, h4 { letter-spacing: .01em; }

/* ---- ヒーロー（ページ上部の大きな見出し） ---- */
.hero {
  border-radius: 28px; padding: 40px 36px; color: #fff; position: relative; overflow: hidden;
  background: linear-gradient(135deg, #5b4fe0 0%, #7c4ddb 45%, #e0569b 100%);
  box-shadow: 0 18px 40px -18px rgba(91,79,224,.55);
}
.hero::after {  /* 右上の飾りの円 */
  content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px;
  border-radius: 50%; background: rgba(255,255,255,.12);
}
.hero .hero-emoji { font-size: 3rem; line-height: 1; }
.hero h1 { color: #fff; font-size: 2.6rem; font-weight: 800; margin: 10px 0 6px; padding: 0; }
.hero p { color: rgba(255,255,255,.92); font-size: 1.08rem; margin: 0; }
.hero.small { padding: 22px 28px; border-radius: 22px; }
.hero.small h1 { font-size: 1.8rem; margin: 4px 0 2px; }
.hero.small .hero-emoji { font-size: 2rem; }
.hero.tm { background: linear-gradient(135deg, #3d5afe 0%, #5b4fe0 50%, #8e44d6 100%); }
.hero.rt { background: linear-gradient(135deg, #0f9b8e 0%, #1a7fd1 60%, #3d5afe 100%); }
.hero.doc { background: linear-gradient(135deg, #f08a3c 0%, #e0569b 100%); }

/* ---- 使い方の3ステップ ---- */
.steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 22px 0 6px; }
.step { background: #fff; border: 1px solid #e2e4f0; border-radius: 18px; padding: 16px 18px; }
.step .num { display: inline-block; width: 28px; height: 28px; border-radius: 50%; background: #eceafd;
  color: #5b4fe0; font-weight: 800; text-align: center; line-height: 28px; margin-right: 8px; }
.step b { font-size: 1.02rem; }
.step div { color: #5a5d75; font-size: .9rem; margin-top: 6px; }

/* ---- カード（st.container(key="card_...") に適用） ---- */
[class*="st-key-card_"], [class*="st-key-mode_"] {
  background: #fff; border: 1px solid #e2e4f0; border-radius: 20px; padding: 18px 18px 14px;
  box-shadow: 0 2px 10px rgba(29,31,51,.04); transition: box-shadow .15s, transform .15s;
}
[class*="st-key-card_"]:hover, [class*="st-key-mode_"]:hover {
  box-shadow: 0 10px 26px -10px rgba(91,79,224,.35); transform: translateY(-2px);
}
[class*="st-key-mode_"] { padding: 26px 26px 20px; }
.mode-emoji { font-size: 2.6rem; }
.mode-title { font-size: 1.45rem; font-weight: 800; margin: 6px 0 4px; }
.mode-desc { color: #5a5d75; margin-bottom: 10px; }
.mode-points { margin: 0 0 12px; padding-left: 1.1em; color: #34374f; }
.continue { background: #f0effd; color: #4a3fcf; border-radius: 12px; padding: 8px 12px; font-size: .9rem; margin-bottom: 10px; }

/* ---- 銘柄カード ---- */
.badges { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.badge { font-size: .72rem; font-weight: 700; padding: 2px 9px; border-radius: 999px; }
.badge.jp { background: #fdeceb; color: #b4372f; }
.badge.us { background: #e7f0fc; color: #1f5fae; }
.badge.etf { background: #fff3dc; color: #95600a; }
.badge.own { background: #e3f6ec; color: #0b7d3e; }
.stock-name { font-weight: 800; font-size: 1.05rem; line-height: 1.3; }
.stock-code { color: #8a8da3; font-size: .8rem; }
.stock-desc { color: #5a5d75; font-size: .84rem; line-height: 1.5; height: 3em; margin: 4px 0 8px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.stock-price { font-size: 1.35rem; font-weight: 800; }
.stock-sub { color: #8a8da3; font-size: .8rem; }
.chg { font-weight: 700; font-size: .92rem; }

/* ---- 数値タイル（KPI） ---- */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 8px 0 4px; }
.kpi { background: #fff; border: 1px solid #e2e4f0; border-radius: 20px; padding: 16px 20px; }
.kpi.main { background: linear-gradient(135deg, #5b4fe0, #7c4ddb); border: none; color: #fff; }
.kpi .label { font-size: .85rem; color: #5a5d75; }
.kpi.main .label { color: rgba(255,255,255,.85); }
.kpi .value { font-size: 1.65rem; font-weight: 800; margin-top: 2px; }
.kpi .sub { font-size: .86rem; margin-top: 2px; color: #5a5d75; }
.kpi.main .sub { color: #fff; }

/* ---- 成績くらべ ---- */
.versus { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; background: #fff;
  border: 1px solid #e2e4f0; border-radius: 16px; padding: 10px 16px; margin: 10px 0 2px; font-size: .92rem; }
.versus .vs-item { padding: 2px 4px; }
.versus .verdict { margin-left: auto; font-weight: 800; }

/* ---- タイムマシンの操作パネル ---- */
.st-key-tm_panel { background: #1d1f33; border-radius: 24px; padding: 22px 26px; color: #fff; }
.st-key-tm_panel p, .st-key-tm_panel span { color: #fff; }
.tm-now-label { color: #b9b6ff; font-size: .9rem; font-weight: 700; letter-spacing: .1em; }
.tm-now { font-size: 2.4rem; font-weight: 800; line-height: 1.15; }
.tm-range { color: #a9abc4 !important; font-size: .85rem; margin-top: 6px; }
.tm-bar { height: 8px; background: #34375a; border-radius: 99px; margin-top: 12px; overflow: hidden; }
.tm-bar > div { height: 100%; background: linear-gradient(90deg, #7c8cff, #e0569b); border-radius: 99px; }

/* ---- スマホなど狭い画面 ---- */
@media (max-width: 640px) {
  .hero { padding: 26px 22px; border-radius: 22px; }
  .hero h1 { font-size: 1.7rem; }
  .hero.small h1 { font-size: 1.4rem; }
  .tm-now { font-size: 1.8rem; }
  .kpi .value { font-size: 1.4rem; }
}

/* ---- 画面上部のナビゲーション ---- */
.st-key-topnav { margin-bottom: 6px; }
.footer-note { color: #8a8da3; font-size: .8rem; margin-top: 28px; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def esc(text: str) -> str:
    return html.escape(text)


def hero(emoji: str, title: str, subtitle: str, variant: str = "") -> None:
    st.markdown(
        f'<div class="hero {variant}"><div class="hero-emoji">{emoji}</div>'
        f"<h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )


def change_html(ratio: float | None, suffix: str = "") -> str:
    """変化率を ▲+1.2% / ▼-3.4% の色付き表示にする"""
    if ratio is None:
        return '<span class="chg" style="color:#8a8da3">－</span>'
    pct = round(ratio * 100, 1) + 0.0
    if pct > 0:
        return f'<span class="chg" style="color:{UP}">▲ +{pct:.1f}%{suffix}</span>'
    if pct < 0:
        return f'<span class="chg" style="color:{DOWN}">▼ {pct:.1f}%{suffix}</span>'
    return f'<span class="chg" style="color:#5a5d75">± 0.0%{suffix}</span>'


def money_change_html(amount: float, ratio: float | None = None, color: bool = True) -> str:
    """損益額（と率）を ▲+12,345円（+1.2%） の形式にする"""
    sign = "▲ +" if amount > 0.5 else ("▼ " if amount < -0.5 else "± ")
    text = f"{sign}{amount:,.0f}円" if abs(amount) > 0.5 else "± 0円"
    if ratio is not None:
        text += f"（{round(ratio * 100, 1) + 0.0:+.1f}%）"
    if not color:
        return text
    c = UP if amount > 0.5 else (DOWN if amount < -0.5 else "#5a5d75")
    return f'<span style="color:{c};font-weight:700">{text}</span>'


def kpis(items: list[dict]) -> None:
    """数値タイルを横に並べる。items: [{"label", "value", "sub", "main"(省略可)}]"""
    cells = "".join(
        f'<div class="kpi{" main" if it.get("main") else ""}"><div class="label">{esc(it["label"])}</div>'
        f'<div class="value">{it["value"]}</div><div class="sub">{it.get("sub", "")}</div></div>'
        for it in items
    )
    st.markdown(f'<div class="kpis">{cells}</div>', unsafe_allow_html=True)
