"""グラフ（Altair）。色は銘柄ごとに固定し、どのグラフでも同じ銘柄は同じ色になるようにする"""

import altair as alt
import pandas as pd

# 色覚の違いに配慮して検証済みの8色（この順番で割り当てる）
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
OTHER = "#9a9cb0"  # 9銘柄目以降・「その他」用
CASH = "#c9cbd9"  # 現金
GRID = "#e8e9f1"
AXIS_LABEL = "#7d8098"

YEN_AXIS = "format(datum.value / 10000, ',.0f') + '万円'"


def _style(chart: alt.Chart, height: int) -> alt.Chart:
    return (
        chart.properties(height=height)
        .configure_view(strokeWidth=0)
        .configure_axis(gridColor=GRID, domain=False, tickColor=GRID, labelColor=AXIS_LABEL, labelFontSize=11)
        .configure_legend(labelFontSize=12, symbolStrokeWidth=3, orient="top", title=None, labelLimit=220, columnPadding=24)
    )


def _to_dates(index) -> pd.DatetimeIndex:
    return pd.to_datetime(pd.Index(index))


def asset_chart(df: pd.DataFrame, date_format: str) -> alt.Chart:
    """資産の推移。1列目が自分の資産（面＋実線）、残りは比較用の指数（破線）"""
    names = list(df.columns)
    d = df.copy()
    d.index = _to_dates(d.index)
    d.index.name = "date"
    wide = d.reset_index()
    long = wide.melt("date", var_name="series", value_name="value")

    color = alt.Color("series:N", scale=alt.Scale(domain=names, range=PALETTE[: len(names)]), legend=alt.Legend())
    dash = alt.StrokeDash("series:N", scale=alt.Scale(domain=names, range=[[1, 0]] + [[6, 4]] * (len(names) - 1)), legend=None)
    x = alt.X("date:T", title=None, axis=alt.Axis(format=date_format, grid=False, labelAngle=0))
    y = alt.Y("value:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(labelExpr=YEN_AXIS, tickCount=5))

    area = (
        alt.Chart(long).transform_filter(alt.datum.series == names[0])
        .mark_area(clip=True, opacity=1, line=False,
                   color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                                      stops=[alt.GradientStop(color="rgba(42,120,214,0.02)", offset=0),
                                             alt.GradientStop(color="rgba(42,120,214,0.22)", offset=1)]))
        .encode(x=x, y=y)
    )
    lines = alt.Chart(long).mark_line(strokeWidth=2.2).encode(x=x, y=y, color=color, strokeDash=dash)

    # マウスを乗せた時点の値をまとめて表示する（縦線＋ツールチップ）
    hover = alt.selection_point(fields=["date"], nearest=True, on="pointerover", empty=False, clear="pointerout")
    tips = [alt.Tooltip("date:T", title="時点", format=date_format)] + [
        alt.Tooltip(field=n, type="quantitative", title=n, format=",.0f") for n in names
    ]
    rule = (
        alt.Chart(wide).mark_rule(color="#b5b7c8", strokeWidth=1)
        .encode(x="date:T", opacity=alt.condition(hover, alt.value(1), alt.value(0)), tooltip=tips)
        .add_params(hover)
    )
    points = (
        alt.Chart(long).mark_point(filled=True, size=70, stroke="white", strokeWidth=2)
        .encode(x=x, y=y, color=color).transform_filter(hover)
    )
    return _style(alt.layer(area, lines, rule, points), 300)


def allocation_donut(items: list[tuple[str, float, str]]) -> alt.Chart:
    """資産の内訳。items: [(名前, 金額, 色)]"""
    total = sum(v for _, v, _ in items) or 1
    df = pd.DataFrame([{"name": n, "value": v, "pct": v / total} for n, v, _ in items])
    names = [n for n, _, _ in items]
    colors = [c for _, _, c in items]
    chart = (
        alt.Chart(df).mark_arc(innerRadius=62, outerRadius=105, stroke="white", strokeWidth=2, cornerRadius=4)
        .encode(
            theta=alt.Theta("value:Q", stack=True),
            color=alt.Color("name:N", scale=alt.Scale(domain=names, range=colors),
                            legend=alt.Legend(orient="right", columns=1)),
            order=alt.Order("value:Q", sort="descending"),
            tooltip=[alt.Tooltip("name:N", title="内訳"), alt.Tooltip("value:Q", title="金額（円）", format=",.0f"),
                     alt.Tooltip("pct:Q", title="割合", format=".1%")],
        )
    )
    return (
        chart.properties(height=240)
        .configure_view(strokeWidth=0)
        .configure_legend(labelFontSize=12, title=None, labelLimit=200, symbolType="circle")
    )


def performance_chart(series: dict[str, pd.Series], colors: dict[str, str], date_format: str) -> alt.Chart:
    """保有銘柄ごとの値動き（買い始めた時点を 0% とした変化率）"""
    frames = []
    for name, s in series.items():
        frames.append(pd.DataFrame({"date": _to_dates(s.index), "name": name, "pct": (s / s.iloc[0] - 1).values}))
    df = pd.concat(frames)
    names = list(series)
    color = alt.Color("name:N", scale=alt.Scale(domain=names, range=[colors[n] for n in names]), legend=alt.Legend())
    x = alt.X("date:T", title=None, axis=alt.Axis(format=date_format, grid=False, labelAngle=0))
    y = alt.Y("pct:Q", title=None, axis=alt.Axis(format="+.0%", tickCount=5))
    hover = alt.selection_point(fields=["date"], nearest=True, on="pointerover", empty=False, clear="pointerout")
    lines = alt.Chart(df).mark_line(strokeWidth=2).encode(x=x, y=y, color=color)
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#9a9cb0", strokeDash=[3, 3]).encode(y="y:Q")
    points = (
        alt.Chart(df).mark_point(filled=True, size=60, stroke="white", strokeWidth=1.5)
        .encode(x=x, y=y, color=color,
                tooltip=[alt.Tooltip("name:N", title="銘柄"), alt.Tooltip("date:T", title="時点", format=date_format),
                         alt.Tooltip("pct:Q", title="買い始めからの変化", format="+.1%")],
                opacity=alt.condition(hover, alt.value(1), alt.value(0)))
        .add_params(hover)
    )
    return _style(alt.layer(zero, lines, points), 260)


def price_chart(s: pd.Series, color: str, date_format: str, height: int = 220) -> alt.Chart:
    """1銘柄の株価の推移（円換算）"""
    df = pd.DataFrame({"date": _to_dates(s.index), "price": s.values})
    x = alt.X("date:T", title=None, axis=alt.Axis(format=date_format, grid=False, labelAngle=0))
    y = alt.Y("price:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(format=",.0f", tickCount=4))
    area = alt.Chart(df).mark_area(clip=True, color=color, opacity=0.12).encode(x=x, y=y)
    line = alt.Chart(df).mark_line(strokeWidth=2, color=color).encode(x=x, y=y)
    hover = alt.selection_point(fields=["date"], nearest=True, on="pointerover", empty=False, clear="pointerout")
    points = (
        alt.Chart(df).mark_point(filled=True, size=60, color=color, stroke="white", strokeWidth=1.5)
        .encode(x=x, y=y, opacity=alt.condition(hover, alt.value(1), alt.value(0)),
                tooltip=[alt.Tooltip("date:T", title="時点", format=date_format),
                         alt.Tooltip("price:Q", title="株価（円）", format=",.0f")])
        .add_params(hover)
    )
    return _style(alt.layer(area, line, points), height)


def sparkline(s: pd.Series, color: str) -> alt.Chart:
    """カードに入れる小さな株価グラフ（軸なし）"""
    df = pd.DataFrame({"i": range(len(s)), "v": s.values})
    y = alt.Y("v:Q", scale=alt.Scale(zero=False), axis=None)
    x = alt.X("i:Q", axis=None)
    area = alt.Chart(df).mark_area(clip=True, color=color, opacity=0.12).encode(x=x, y=y)
    line = alt.Chart(df).mark_line(strokeWidth=2, color=color).encode(x=x, y=y)
    return alt.layer(area, line).properties(height=64).configure_view(strokeWidth=0)
