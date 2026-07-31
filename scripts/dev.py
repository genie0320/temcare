#!/usr/bin/env python3
"""올라케어 개발 서버 기동. `make dev` 또는 `python scripts/dev.py [admin|app]`으로 실행한다.

백엔드(Django)와 프론트(관리자 또는 고객, 기본값 admin) 하나를 동시에 띄운다.
Make의 셸 차이(Windows/Mac/Linux) 문제를 피하려고 실제 기동 로직은 여기 파이썬에 둔다.

저사양 환경 팁(docs/08_tech_stack.md §6): 두 프론트를 동시에 띄우지 않는다.
지금 안 쓰는 프론트를 보고 싶으면 Ctrl+C로 끄고 다른 인자로 다시 실행할 것.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IS_WINDOWS = sys.platform == "win32"


def npm_cmd() -> str:
    return "npm.cmd" if IS_WINDOWS else "npm"


def main() -> int:
    front = sys.argv[1] if len(sys.argv) > 1 else "admin"
    if front not in ("admin", "app"):
        print(f"알 수 없는 프론트: {front!r} — admin 또는 app만 가능")
        return 1

    front_dir = ROOT / f"{front}-web"
    if not front_dir.exists():
        print(f"{front_dir} 가 없다. 저장소 뼈대가 온전한지 확인할 것.")
        return 1

    procs: list[subprocess.Popen] = []
    try:
        print("[dev] 백엔드(Django) 기동…")
        procs.append(
            subprocess.Popen(
                ["uv", "run", "python", "manage.py", "runserver", "8000"],
                cwd=ROOT / "backend",
            )
        )

        print(f"[dev] 프론트({front}-web) 기동…")
        frontend = subprocess.Popen([npm_cmd(), "run", "dev"], cwd=front_dir)
        procs.append(frontend)

        frontend.wait()
    except KeyboardInterrupt:
        print("\n[dev] 종료 중…")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
