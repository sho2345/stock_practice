"""資産（現金・保有株・取引履歴）を管理するロジック。画面表示とは切り離している"""

from dataclasses import asdict, dataclass, field


class TradeError(Exception):
    """売買できないとき（お金が足りない・株が足りないなど）に投げる例外"""


@dataclass
class Holding:
    shares: int  # 保有株数
    cost: float  # 購入にかかった合計金額（円）。平均取得単価 = cost / shares
    split_checked: str = ""  # 株式分割をどの日付まで反映済みか（リアルタイムモード用）

    @property
    def avg_cost(self) -> float:
        return self.cost / self.shares if self.shares else 0.0


@dataclass
class Portfolio:
    initial_cash: float  # 元手
    cash: float  # 現在の現金
    holdings: dict[str, Holding] = field(default_factory=dict)
    trades: list[dict] = field(default_factory=list)  # 取引履歴
    realized: float = 0.0  # 売却して確定した損益の合計

    def buy(self, code: str, shares: int, price: float, date: str, native_price: float | None = None) -> None:
        """price は 1 株あたりの円換算価格。native_price は米国株のドル価格（記録用）"""
        if shares <= 0:
            raise TradeError("株数は 1 以上を指定してください。")
        amount = shares * price
        if amount > self.cash + 1e-6:
            raise TradeError(f"現金が足りません（必要: {amount:,.0f}円 / 現金: {self.cash:,.0f}円）。")
        self.cash -= amount
        h = self.holdings.get(code)
        if h is None:
            self.holdings[code] = Holding(shares=shares, cost=amount, split_checked=date)
        else:
            h.shares += shares
            h.cost += amount
            h.split_checked = max(h.split_checked, date)
        self._log("買い", code, shares, price, amount, date, native_price)

    def sell(self, code: str, shares: int, price: float, date: str, native_price: float | None = None) -> float:
        """売却して、この取引で確定した損益（円）を返す"""
        if shares <= 0:
            raise TradeError("株数は 1 以上を指定してください。")
        h = self.holdings.get(code)
        if h is None or h.shares < shares:
            owned = h.shares if h else 0
            raise TradeError(f"保有株数が足りません（保有: {owned}株）。")
        amount = shares * price
        # 売った株数の分だけ取得金額を減らす（平均取得単価で計算）
        cost_part = h.avg_cost * shares
        profit = amount - cost_part
        h.shares -= shares
        h.cost -= cost_part
        if h.shares == 0:
            del self.holdings[code]
        self.cash += amount
        self.realized += profit
        self._log("売り", code, shares, price, amount, date, native_price, profit)
        return profit

    def apply_split(self, code: str, ratio: float, date: str) -> None:
        """株式分割を反映する（例：1株→5株なら ratio=5）。取得金額の合計は変わらない"""
        h = self.holdings.get(code)
        if h is None:
            return
        before = h.shares
        h.shares = int(round(h.shares * ratio))
        self.trades.append({
            "date": date, "side": "株式分割", "code": code,
            "shares": h.shares - before, "price": None, "amount": 0.0,
            "note": f"1株→{ratio:g}株の分割（{before}株→{h.shares}株）",
        })

    def market_value(self, prices: dict[str, float]) -> float:
        """保有株の評価額の合計（prices は銘柄コード→1株の円換算価格）"""
        return sum(h.shares * prices[code] for code, h in self.holdings.items())

    def total_value(self, prices: dict[str, float]) -> float:
        return self.cash + self.market_value(prices)

    def _log(self, side, code, shares, price, amount, date, native_price, profit=None) -> None:
        self.trades.append({
            "date": date, "side": side, "code": code, "shares": shares,
            "price": price, "native_price": native_price, "amount": amount, "profit": profit,
        })

    # ---- JSON 保存用の変換 ----
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Portfolio":
        return cls(
            initial_cash=d["initial_cash"],
            cash=d["cash"],
            holdings={k: Holding(**v) for k, v in d["holdings"].items()},
            trades=d["trades"],
            realized=d.get("realized", 0.0),
        )
