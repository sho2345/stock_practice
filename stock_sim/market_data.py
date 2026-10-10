"""株価データの取得（yfinance を利用。無料・API キー不要）"""

from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

from .stocks import STOCK_BY_CODE, all_codes

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MONTHLY_CSV = DATA_DIR / "prices_monthly.csv"

FX = "JPY=X"  # ドル円レート（1ドル＝何円か）
N225 = "^N225"  # 日経平均株価
SP500 = "^GSPC"  # S&P500
DATA_START = "2005-01-01"


def _download_close(tickers: list[str], **kwargs) -> pd.DataFrame:
    # threads=True だと yfinance 内部のキャッシュで "database is locked" が起きるため順番に取得する
    raw = yf.download(tickers, progress=False, threads=False, **kwargs)
    return raw["Close"]


# ======================= タイムマシンモード用（月ごとの終値） =======================

def fetch_monthly_prices() -> list[str]:
    """月ごとの終値を取得して CSV に保存する。取得に失敗した銘柄コードの一覧を返す"""
    tickers = all_codes() + [FX, N225, SP500]
    # auto_adjust=True: 株式分割・配当を反映した「調整後株価」を使う
    close = _download_close(tickers, start=DATA_START, interval="1mo", auto_adjust=True)
    # 今月はまだ終わっておらず値が確定していないので除く
    this_month = pd.Timestamp.today().to_period("M").to_timestamp()
    close = close[close.index < this_month]
    close = close.ffill()  # 祝日などによる欠損を直前の値で埋める（上場前の空欄は埋めない）
    close.index = close.index.strftime("%Y-%m")
    close.index.name = "month"
    failed = [t for t in tickers if t not in close.columns or close[t].isna().all()]
    if FX in failed or N225 in failed:
        raise RuntimeError("為替または日経平均のデータが取得できませんでした。時間をおいて再試行してください。")
    DATA_DIR.mkdir(exist_ok=True)
    close.to_csv(MONTHLY_CSV)
    load_monthly_prices.clear()
    return failed


@st.cache_data(show_spinner=False)
def load_monthly_prices() -> pd.DataFrame | None:
    """保存済みの月次データを読み込む（行: "YYYY-MM"、列: 銘柄コード）。未取得なら None"""
    if not MONTHLY_CSV.exists():
        return None
    return pd.read_csv(MONTHLY_CSV, index_col="month")


def missing_codes(df: pd.DataFrame) -> list[str]:
    """銘柄一覧にあるのに、保存済みデータに列がない銘柄（銘柄を追加した後、データが古いままのとき）"""
    return [c for c in all_codes() if c not in df.columns]


def monthly_price_jpy(df: pd.DataFrame, code: str, month: str) -> float | None:
    """その月の 1 株の円換算価格。上場前などで値がなければ None"""
    if code not in df.columns:
        return None
    v = df.at[month, code]
    if pd.isna(v):
        return None
    if STOCK_BY_CODE[code].market == "US":
        v *= df.at[month, FX]
    return float(v)


def monthly_series_jpy(df: pd.DataFrame, code: str, until: str) -> pd.Series:
    """until の月までの円換算株価の推移（未来の値は含めない）"""
    if code not in df.columns:
        return pd.Series(dtype=float)
    s = df.loc[:until, code]
    if STOCK_BY_CODE[code].market == "US":
        s = s * df.loc[:until, FX]
    return s.dropna()


# ======================= リアルタイムモード用（最新の株価） =======================

@st.cache_data(ttl=1800, show_spinner="最新の株価を取得しています…")
def fetch_latest_prices() -> dict[str, dict]:
    """全銘柄の最新株価。{コード: {"price": 現地通貨の価格, "prev": 前日の終値, "date": "YYYY-MM-DD"}}
    取引時間中は約15〜20分遅れの値、時間外は直近の終値になる。30分間キャッシュする"""
    tickers = all_codes() + [FX, N225, SP500]
    close = _download_close(tickers, period="10d", interval="1d", auto_adjust=False)
    result = {}
    for t in tickers:
        if t not in close.columns:
            continue
        s = close[t].dropna()
        if not s.empty:
            prev = float(s.iloc[-2]) if len(s) >= 2 else None
            result[t] = {"price": float(s.iloc[-1]), "prev": prev, "date": s.index[-1].strftime("%Y-%m-%d")}
    return result


def latest_price_jpy(latest: dict[str, dict], code: str) -> float | None:
    if code not in latest:
        return None
    p = latest[code]["price"]
    if STOCK_BY_CODE[code].market == "US":
        if FX not in latest:
            return None
        p *= latest[FX]["price"]
    return p


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_splits(code: str) -> list[tuple[str, float]]:
    """株式分割の履歴 [(日付, 分割比率), ...]。1日キャッシュする"""
    s = yf.Ticker(code).splits
    return [(d.strftime("%Y-%m-%d"), float(r)) for d, r in s.items()]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_daily_history_jpy(code: str, start: str) -> pd.Series:
    """start 以降の日ごとの終値（円換算）。米国株はその日のドル円レートで換算する"""
    tickers = [code, FX] if STOCK_BY_CODE[code].market == "US" else [code]
    close = _download_close(tickers, start=start, interval="1d", auto_adjust=False)
    s = close[code]
    if STOCK_BY_CODE[code].market == "US":
        # 日米で休日が違うため、為替は直前の値で埋めてから掛ける
        s = s * close[FX].ffill().bfill()
    s = s.dropna()
    s.index = s.index.strftime("%Y-%m-%d")
    return s
