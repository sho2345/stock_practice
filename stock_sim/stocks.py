"""シミュレータで売買できる銘柄の一覧"""

from dataclasses import dataclass


# ETF（指数にまとめて投資できる商品）の銘柄コード
ETF_CODES = {"1321.T", "SPY", "QQQ"}


@dataclass(frozen=True)
class Stock:
    code: str  # yfinance で使う銘柄コード（日本株は末尾に .T）
    name: str
    market: str  # "JP"（日本・円建て） または "US"（米国・ドル建て）
    description: str
    short: str = ""  # グラフの凡例などに使う短い名前（省略時は name の括弧より前）

    @property
    def short_name(self) -> str:
        return self.short or self.name.split("（")[0]

    @property
    def category(self) -> str:
        """画面上の分類：日本株 / 米国株 / ETF"""
        if self.code in ETF_CODES:
            return "ETF"
        return "日本株" if self.market == "JP" else "米国株"


STOCKS: list[Stock] = [
    # ---- 日本株 ----
    Stock("7203.T", "トヨタ自動車", "JP", "世界最大級の自動車メーカー"),
    Stock("7267.T", "本田技研工業（ホンダ）", "JP", "自動車・二輪車メーカー"),
    Stock("6758.T", "ソニーグループ", "JP", "ゲーム（PlayStation）・音楽・映画・半導体センサー"),
    Stock("7974.T", "任天堂", "JP", "ゲーム機・ゲームソフト（Switch、マリオなど）"),
    Stock("9983.T", "ファーストリテイリング", "JP", "ユニクロ・GU を展開するアパレル企業"),
    Stock("9984.T", "ソフトバンクグループ", "JP", "国内外の IT 企業へ投資する投資会社"),
    Stock("6861.T", "キーエンス", "JP", "工場向けセンサーなど。非常に利益率が高いことで有名"),
    Stock("8035.T", "東京エレクトロン", "JP", "半導体を作るための製造装置メーカー"),
    Stock("6501.T", "日立製作所", "JP", "電機・IT システム・社会インフラ"),
    Stock("4063.T", "信越化学工業", "JP", "半導体の材料（シリコンウエハー）や塩化ビニル"),
    Stock("8306.T", "三菱UFJフィナンシャル・グループ", "JP", "日本最大の銀行グループ", short="三菱UFJ"),
    Stock("8058.T", "三菱商事", "JP", "総合商社。資源・食品・インフラなど幅広く事業を行う"),
    Stock("9432.T", "NTT", "JP", "通信大手（ドコモなど）"),
    Stock("9433.T", "KDDI", "JP", "通信大手（au）"),
    Stock("2914.T", "日本たばこ産業（JT）", "JP", "たばこ・食品。配当が多いことで有名"),
    Stock("4502.T", "武田薬品工業", "JP", "国内最大手の製薬会社"),
    Stock("4661.T", "オリエンタルランド", "JP", "東京ディズニーリゾートの運営会社"),
    Stock("285A.T", "キオクシアホールディングス", "JP", "スマホや PC のデータを保存する半導体メモリ（NAND）。2024年12月上場", short="キオクシア"),
    Stock("6857.T", "アドバンテスト", "JP", "半導体が正しく動くかを調べる検査装置で世界トップ級"),
    Stock("6920.T", "レーザーテック", "JP", "最先端の半導体向けの検査装置。株価の値動きが大きいことで有名"),
    Stock("7011.T", "三菱重工業", "JP", "発電設備・防衛・ロケットなど。重工業の最大手"),
    Stock("8316.T", "三井住友フィナンシャルグループ", "JP", "三井住友銀行を中心とする大手銀行グループ", short="三井住友FG"),
    Stock("6098.T", "リクルートホールディングス", "JP", "求人サイト Indeed・SUUMO・ホットペッパーなど", short="リクルート"),
    Stock("4385.T", "メルカリ", "JP", "フリマアプリ「メルカリ」・決済サービス「メルペイ」"),
    Stock("4755.T", "楽天グループ", "JP", "ネット通販・楽天カード・楽天モバイルなど"),
    Stock("7832.T", "バンダイナムコホールディングス", "JP", "ガンプラ・ドラゴンボールなどのおもちゃ・ゲーム", short="バンダイナムコ"),
    Stock("3382.T", "セブン&アイ・ホールディングス", "JP", "コンビニのセブン-イレブンやイトーヨーカドー", short="セブン&アイ"),
    Stock("6367.T", "ダイキン工業", "JP", "エアコンで世界トップクラスのメーカー"),
    # ---- 米国株 ----
    Stock("AAPL", "Apple（アップル）", "US", "iPhone・Mac などを開発"),
    Stock("MSFT", "Microsoft（マイクロソフト）", "US", "Windows・Office・クラウド（Azure）"),
    Stock("NVDA", "NVIDIA（エヌビディア）", "US", "AI 向け半導体（GPU）で世界トップ"),
    Stock("AMZN", "Amazon（アマゾン）", "US", "ネット通販・クラウド（AWS）"),
    Stock("GOOGL", "Alphabet（グーグル）", "US", "検索・広告・YouTube"),
    Stock("META", "Meta（メタ）", "US", "Facebook・Instagram"),
    Stock("TSLA", "Tesla（テスラ）", "US", "電気自動車メーカー"),
    Stock("NFLX", "Netflix（ネットフリックス）", "US", "動画配信サービス"),
    Stock("KO", "Coca-Cola（コカ・コーラ）", "US", "飲料。長年配当を増やし続けていることで有名"),
    Stock("MCD", "McDonald's（マクドナルド）", "US", "ハンバーガーチェーン"),
    Stock("DIS", "Walt Disney（ディズニー）", "US", "映画・テーマパーク・動画配信"),
    Stock("AVGO", "Broadcom（ブロードコム）", "US", "通信・AI 向けの半導体。AI ブームで急成長"),
    Stock("AMD", "AMD", "US", "PC・データセンター向けの CPU や GPU。NVIDIA のライバル"),
    Stock("TSM", "TSMC", "US", "台湾の世界最大の半導体受託製造会社。米国市場に上場している株（ADR）を売買"),
    Stock("PLTR", "Palantir（パランティア）", "US", "データ分析・AI ソフトウェア。2020年上場"),
    Stock("COST", "Costco（コストコ）", "US", "会員制の大型倉庫店"),
    Stock("V", "Visa（ビザ）", "US", "世界最大のクレジットカード決済ネットワーク"),
    Stock("BRK-B", "Berkshire Hathaway（バークシャー・ハサウェイ）", "US", "投資の神様ウォーレン・バフェットが率いる投資会社", short="バークシャー"),
    Stock("NKE", "Nike（ナイキ）", "US", "スポーツ用品の世界最大手"),
    # ---- ETF（指数にまとめて投資できる商品） ----
    Stock("1321.T", "日経225連動型上場投資信託（ETF）", "JP", "日経平均株価と同じように動く。日本の代表的な225社にまとめて投資", short="日経225 ETF"),
    Stock("SPY", "SPDR S&P500 ETF", "US", "米国の代表的な500社（S&P500）にまとめて投資", short="S&P500 ETF"),
    Stock("QQQ", "Invesco QQQ（ナスダック100 ETF）", "US", "Apple・NVIDIA などハイテク中心の米国100社にまとめて投資", short="ナスダック100 ETF"),
]

STOCK_BY_CODE: dict[str, Stock] = {s.code: s for s in STOCKS}


def all_codes() -> list[str]:
    return [s.code for s in STOCKS]


def display_name(code: str) -> str:
    """選択肢などに表示する名前（例：[日本] トヨタ自動車 (7203)）"""
    s = STOCK_BY_CODE[code]
    country = "日本" if s.market == "JP" else "米国"
    return f"[{country}] {s.name} ({code.removesuffix('.T')})"


def yahoo_url(code: str) -> str:
    """Yahoo!ファイナンス（日本版）の銘柄ページ。ニュースや業績を確認する用"""
    return f"https://finance.yahoo.co.jp/quote/{code}"
