# 📈 はじめての株シミュレータ

株を知らない人向けに、**実際の株価データ** を使って、お金を使わずに株の売買を体験できる Web アプリです（Python + Streamlit）。

- **⏳ タイムマシンモード**：2005年以降の好きな時点に戻り、時間を早送りしながら投資する
- **📡 リアルタイムモード**：今日の株価で売買し、数か月後・数年後に結果を確かめる
- 日本株・米国株・ETF の50銘柄。米国株はドル円レートで円に換算
- 「株の基礎知識」「アプリの使い方」のマニュアル付き

株価は [yfinance](https://github.com/ranaroussi/yfinance) を使って Yahoo! Finance から無料で取得しています（非公式のツールです）。

---

## 自分の PC で使う

1. [Python](https://www.python.org/)（3.10 以上）をインストールする
2. このフォルダの **`起動.bat` をダブルクリック** する
   - 初回だけ、必要なライブラリのインストールに数分かかります
   - ブラウザが開いてアプリが表示されます。黒い画面を閉じるとアプリも終了します

この使い方では **ログインはなく**、売買記録はこの PC の `data/saves/` に保存されます（ローカルモード）。

> 同じ Wi-Fi につながっているスマホからも使えます。黒い画面に表示される `Network URL`（例：`http://192.168.x.x:8501`）をスマホのブラウザで開いてください。

---

## インターネットに公開する（ログイン＋データベース）

公開すると、URL を知っている人なら誰でも、PC やスマホから使えます。各自が **Google アカウントでログイン** し、売買記録は利用者ごとに **データベース** に保存されます。

使うサービスはすべて **無料プラン** です。

| 役割 | サービス | 無料プランの注意点 |
|---|---|---|
| アプリを動かす | [Streamlit Community Cloud](https://streamlit.io/cloud) | しばらく使われないとスリープし、次に開いたとき起動に30秒ほどかかる |
| ログイン | Google（OAuth） | 特になし |
| データベース | [Neon](https://neon.tech/)（PostgreSQL） | 容量 0.5GB（このアプリなら数万人分でも余裕） |

以下の順番で設定します。**手順 3 の URL を手順 4 で使う** ので、順番どおりに進めてください。

### 手順 1：データベースを作る（Neon）

1. https://neon.tech/ にアクセスし、「Sign up」から GitHub アカウントなどで登録する
2. 「Create project」でプロジェクトを作る
   - Project name：`stock-sim` など自由に
   - Region：**AWS US East（N. Virginia）** など米国のものを選ぶ（Streamlit Cloud のサーバーが米国にあるため、近いほうが速い）
3. ダッシュボードの **「Connect」** を押し、表示された接続文字列（`postgresql://...` で始まる文字列）をコピーしてメモしておく

テーブルはアプリが自動で作るので、Neon 側の作業はこれだけです。

### 手順 2：GitHub にコードを置く

このリポジトリが GitHub に上がっていれば OK です。

### 手順 3：Streamlit Community Cloud にデプロイする

1. https://share.streamlit.io/ に GitHub アカウントでログインする
2. 「Create app」→「Deploy a public app from GitHub」を選ぶ
3. 次のように入力する
   - Repository：このリポジトリ
   - Branch：`main`
   - Main file path：`app.py`
   - App URL：好きな名前にする（例：`hajimete-kabu` → `https://hajimete-kabu.streamlit.app`）。**この URL をメモする**
4. 「Advanced settings」で Python のバージョンを **3.12** にする
5. 「Deploy」を押す（この時点ではまだログインの設定が無いので、ローカルモードで動きます。手順 5 の設定で切り替わります）

### 手順 4：Google ログインを設定する（Google Cloud）

1. https://console.cloud.google.com/ にアクセスし、新しいプロジェクトを作る（名前は自由）
2. 左のメニューから **「API とサービス」→「OAuth 同意画面」**（「Google Auth Platform」と表示される場合もあります）を開き、対象（ユーザーの種類）は **外部** にする
3. **「ブランディング」** ページで次を入力し、一番下の **「保存」** を押す（手順 3 の URL が `https://hajimete-kabu.streamlit.app` の場合の例）
   - アプリ名：`はじめての株シミュレータ` など
   - ユーザー サポートメール・デベロッパーの連絡先：自分のメールアドレス（打ち間違いに注意）
   - アプリのロゴ：**空のまま**（ロゴを入れると Google の審査が必要になる）
   - アプリケーションのホームページ：`https://hajimete-kabu.streamlit.app`
   - プライバシー ポリシーのリンク：`https://hajimete-kabu.streamlit.app/privacy`（アプリに含まれているページ）
   - 承認済みドメイン：`hajimete-kabu.streamlit.app`（`streamlit.app` だけでは登録できない）
4. **「対象」→「アプリを公開」** を押して、公開ステータスを **「本番環境」** にする
   - 「テスト」のままだと、自分で登録したテストユーザーしかログインできません
   - このアプリは名前・メールアドレスなどの基本情報しか使わないので、Google の審査は不要です
   - ログイン時に「Google はこのアプリを確認していません」と出ることがあります。「詳細」→「（アプリ名）に移動」で進めます
5. **「クライアント」→「クライアントを作成」** を押し、次のように入力する
   - アプリケーションの種類：**ウェブ アプリケーション**
   - 承認済みのリダイレクト URI：次の2つを追加
     - `https://（手順 3 の URL）/oauth2callback`（例：`https://hajimete-kabu.streamlit.app/oauth2callback`）
     - `http://localhost:8501/oauth2callback`（自分の PC でログインを試す用）
6. 作成後に表示される **クライアント ID** と **クライアント シークレット** をメモする

### 手順 5：接続情報（Secrets）を登録する

1. Streamlit Community Cloud の自分のアプリの「⋮」→ **「Settings」→「Secrets」** を開く
2. 次の内容を貼り付け、`（ ）` の部分を書き換えて「Save」を押す

```toml
[auth]
redirect_uri = "https://（手順 3 の URL）/oauth2callback"
cookie_secret = "（長いランダムな文字列。下の作り方を参照）"
client_id = "（手順 4 のクライアント ID）"
client_secret = "（手順 4 のクライアント シークレット）"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[database]
url = "（手順 1 でコピーした postgresql://... の接続文字列）"
```

`cookie_secret` は、PC で次のコマンドを実行して表示された文字列を使います。

```
python -c "import secrets; print(secrets.token_hex(32))"
```

3. 保存するとアプリが再起動し、ログイン画面が表示されれば完成です 🎉

> ⚠️ これらの値はパスワードと同じです。人に見せたり、GitHub に上げたりしないでください。

### 自分の PC でログイン・データベースを試したいとき

`.streamlit/secrets.toml.example` をコピーして `.streamlit/secrets.toml` という名前にし、値を書き換えてから起動します（`redirect_uri` は `http://localhost:8501/oauth2callback`）。`secrets.toml` は `.gitignore` で除外されているので、GitHub には上がりません。

---

## ファイル構成

| パス | 内容 |
|---|---|
| `app.py` | 入口（ログインの確認と画面の切り替え） |
| `views/` | 各画面（ホーム・タイムマシン・リアルタイム・マニュアル） |
| `stock_sim/stocks.py` | 売買できる銘柄の一覧（ここに追加すれば銘柄を増やせる） |
| `stock_sim/market_data.py` | 株価の取得 |
| `stock_sim/portfolio.py` | 売買・損益の計算 |
| `stock_sim/storage.py` | 売買記録の保存（データベース または JSON ファイル） |
| `stock_sim/auth.py` | Google ログイン |
| `docs/` | アプリ内で表示するマニュアル |

> このアプリは学習用のシミュレータです。表示される内容は、特定の銘柄の売買をすすめるものではありません。
