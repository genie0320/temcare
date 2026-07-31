#!/usr/bin/env python3
"""올라케어 최초 셋업. `make setup` 또는 `python scripts/setup.py`로 실행한다.

의존성 설치 + 마이그레이션 + 데모 시드까지 한 번에. 언제든 다시 돌려도 안전(멱등)하다.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IS_WINDOWS = sys.platform == "win32"
NPM = "npm.cmd" if IS_WINDOWS else "npm"


def run(cmd: list[str], cwd: Path) -> None:
    print(f"[setup] ({cwd.name}) {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    run(["uv", "sync"], ROOT / "backend")
    run(["uv", "run", "python", "manage.py", "migrate"], ROOT / "backend")
    run(["uv", "run", "python", "manage.py", "seed_demo"], ROOT / "backend")
    run([NPM, "install"], ROOT / "admin-web")
    run([NPM, "install"], ROOT / "app-web")
    print("\n[setup] 완료. `make dev`(관리자) 또는 `make dev-app`(고객)으로 시작할 것.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
