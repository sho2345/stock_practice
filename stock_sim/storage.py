"""シミュレーションの状態を JSON ファイルに保存・読み込みする（データベースは使わない）"""

import json
from pathlib import Path

SAVE_DIR = Path(__file__).resolve().parent.parent / "data" / "saves"


def load(name: str) -> dict | None:
    path = SAVE_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save(name: str, state: dict) -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    path = SAVE_DIR / f"{name}.json"
    # 書き込み途中で落ちてもファイルが壊れないよう、一時ファイルに書いてから置き換える
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def delete(name: str) -> None:
    (SAVE_DIR / f"{name}.json").unlink(missing_ok=True)
