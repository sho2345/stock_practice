"""シミュレーションの状態を、利用者ごとに保存・読み込みする

保存先は設定によって切り替わる：
- secrets.toml に [database] があるとき：データベース（PostgreSQL など）の saves テーブル
- 無いとき：この PC の data/saves/ にある JSON ファイル（ローカルモード）
どちらでも、呼び出し側は load / save / delete の 3 つを使うだけでよい。
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa
import streamlit as st

from . import auth

SAVE_DIR = Path(__file__).resolve().parent.parent / "data" / "saves"

# 1 行 = 1 人の 1 モード分の状態（JSON 文字列）。データ量は 1 人あたり数十 KB 程度
_TABLE = sa.Table(
    "saves",
    sa.MetaData(),
    sa.Column("user_id", sa.String(255), primary_key=True),
    sa.Column("name", sa.String(50), primary_key=True),  # "time_machine" / "realtime"
    sa.Column("data", sa.Text, nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)


def _db_url() -> str | None:
    try:
        url = st.secrets["database"]["url"] if "database" in st.secrets else None
    except Exception:  # secrets.toml が無いとき
        return None
    return normalize_db_url(url.strip()) if url else None


def normalize_db_url(url: str) -> str:
    """PostgreSQL の接続文字列を、インストール済みのドライバ（psycopg2）を使う形にそろえる

    Neon などでコピーできる接続文字列は postgres:// / postgresql:// / postgresql+psycopg:// など
    書き方がまちまちで、そのままだと入っていないドライバ（psycopg 3）が選ばれて失敗することがあるため
    """
    scheme, sep, rest = url.partition("://")
    if sep and scheme.split("+")[0] in ("postgres", "postgresql"):
        return f"postgresql+psycopg2://{rest}"
    return url  # SQLite など PostgreSQL 以外はそのまま


@st.cache_resource(show_spinner=False)
def _engine(url: str) -> sa.Engine:
    # pool_pre_ping: しばらく使われず切れた接続を自動でつなぎ直す（無料の DB はよく接続を切るため）
    engine = sa.create_engine(url, pool_pre_ping=True)
    _TABLE.metadata.create_all(engine)  # テーブルが無ければ作る
    return engine


# ---- 同じ画面の中で何度も DB に問い合わせないよう、読み込んだ結果をセッションに覚えておく ----
def _cache_key(name: str) -> str:
    return f"_save_{auth.user_id()}_{name}"


def load(name: str) -> dict | None:
    key = _cache_key(name)
    if key not in st.session_state:
        st.session_state[key] = _read(name)
    state = st.session_state[key]
    # 呼び出し側が中身を書き換えても覚えている値が変わらないよう、コピーを返す
    return json.loads(json.dumps(state)) if state is not None else None


def save(name: str, state: dict) -> None:
    _write(name, state)
    st.session_state[_cache_key(name)] = json.loads(json.dumps(state))


def delete(name: str) -> None:
    _remove(name)
    st.session_state[_cache_key(name)] = None


# ======================= 保存先ごとの処理 =======================

def _local_path(name: str) -> Path:
    uid = auth.user_id()
    if uid == auth.LOCAL_USER:
        return SAVE_DIR / f"{name}.json"  # 以前のバージョンと同じ場所（今までの記録をそのまま使える）
    # ログインありで DB が無いとき（動作確認用）は、利用者ごとのフォルダに分ける
    folder = hashlib.sha256(uid.encode()).hexdigest()[:16]
    return SAVE_DIR / folder / f"{name}.json"


def _read(name: str) -> dict | None:
    url = _db_url()
    if url:
        with _engine(url).connect() as conn:
            row = conn.execute(
                sa.select(_TABLE.c.data).where(_TABLE.c.user_id == auth.user_id(), _TABLE.c.name == name)
            ).first()
        return json.loads(row.data) if row else None
    path = _local_path(name)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write(name: str, state: dict) -> None:
    text = json.dumps(state, ensure_ascii=False)
    url = _db_url()
    if url:
        now = datetime.now(timezone.utc)
        where = (_TABLE.c.user_id == auth.user_id()) & (_TABLE.c.name == name)
        with _engine(url).begin() as conn:  # begin(): 最後に自動でコミットされる
            updated = conn.execute(sa.update(_TABLE).where(where).values(data=text, updated_at=now)).rowcount
            if updated == 0:
                conn.execute(sa.insert(_TABLE).values(user_id=auth.user_id(), name=name, data=text, updated_at=now))
        return
    path = _local_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 書き込み途中で落ちてもファイルが壊れないよう、一時ファイルに書いてから置き換える
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _remove(name: str) -> None:
    url = _db_url()
    if url:
        with _engine(url).begin() as conn:
            conn.execute(sa.delete(_TABLE).where(_TABLE.c.user_id == auth.user_id(), _TABLE.c.name == name))
        return
    _local_path(name).unlink(missing_ok=True)
