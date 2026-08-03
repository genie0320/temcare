#!/usr/bin/env python3
"""시연용 공개 주소 띄우기. `make demo` 또는 `python scripts/demo.py`로 실행한다.

원장에게 고객 앱을 보여줘야 할 때, 로컬 개발 서버를 **그 순간만** 공개 HTTPS
주소로 노출한다(docs/08_tech_stack.md §10-0, 결정 #37). 비용 0원이고, 끝나면
Ctrl+C 한 번으로 주소가 사라진다.

    [브라우저] --HTTPS--> [Cloudflare] --터널--> [내 컴퓨터의 Vite 5173]
                                                    └─ /api → Django 8000

터널은 **고객 앱(5173) 하나만** 가리킨다. 관리자(5174)는 회원 개인정보를 다루므로
공개 주소로 내보내지 않는다 — app-web의 vite.config.ts에만 allowedHosts가 있어서
설령 포트를 바꿔 실행해도 관리자는 터널로 열리지 않는다.

★ PUBLIC_DEMO=True로 띄운다. 이게 없으면 시연 링크를 받은 사람 누구나
  /api/accounts/dev-login/ 으로 **비밀번호 없이 관리자**가 될 수 있다(DEBUG 전용
  기능인데 터널 시연도 DEBUG라서 그렇다). settings.py의 PUBLIC_DEMO 주석 참고.
"""

import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IS_WINDOWS = sys.platform == "win32"
APP_PORT = 5173

# cloudflared가 표준출력에 흘리는 임시 도메인. 사람이 로그에서 눈으로 찾기 번거로워
# 여기서 뽑아 크게 찍어준다.
TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

WARNING = """
────────────────────────────────────────────────────────────────
  ⚠  지금 이 주소는 인터넷의 누구나 열 수 있다.

  · **가짜 데이터로만** 시연할 것. 실제 사람의 건강 문진을 받으면
    개인정보 국외이전·보관 문제가 생긴다(docs/08_tech_stack.md §10-1).
  · 시연이 끝나면 **Ctrl+C로 끌 것.** 주소가 즉시 사라진다.
  · 이 창을 닫거나 컴퓨터가 잠들면 주소도 끊긴다 — 정상이다.
────────────────────────────────────────────────────────────────
"""


def npm_cmd() -> str:
    return "npm.cmd" if IS_WINDOWS else "npm"


# winget으로 막 설치한 직후에는 PATH가 갱신되지 않아 shutil.which가 못 찾는다.
# 터미널을 껐다 켜라고 하는 대신 표준 설치 위치를 직접 뒤진다 — 다른 세션이
# 돌고 있어서 창을 못 닫는 상황이 실제로 있었다.
FALLBACK_PATHS = (
    r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
    r"C:\Program Files\cloudflared\cloudflared.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\cloudflared.exe"),
)


def find_cloudflared() -> str | None:
    found = shutil.which("cloudflared")
    if found:
        return found
    if not IS_WINDOWS:
        return None
    return next((p for p in FALLBACK_PATHS if Path(p).exists()), None)


def relay(proc: subprocess.Popen, label: str) -> None:
    """자식 프로세스 출력을 흘리면서 터널 주소만 가로채 크게 찍는다."""
    shown = False
    for raw in proc.stdout:  # type: ignore[union-attr]
        line = raw.rstrip()
        print(f"[{label}] {line}")
        if shown:
            continue
        found = TUNNEL_URL.search(line)
        if found:
            shown = True
            print(f"\n\n  🌐  시연 주소:  {found.group(0)}\n")
            print(WARNING, flush=True)


def main() -> int:
    cloudflared = find_cloudflared()
    if cloudflared is None:
        print(
            "cloudflared 가 없다. 아래로 설치한 뒤 실행할 것:\n"
            "\n    winget install --id Cloudflare.cloudflared\n"
        )
        return 1

    env = {**os.environ, "PUBLIC_DEMO": "True"}

    procs: list[subprocess.Popen] = []
    try:
        print("[demo] 백엔드(Django) 기동 — PUBLIC_DEMO=True")
        procs.append(
            subprocess.Popen(
                ["uv", "run", "python", "manage.py", "runserver", "8000"],
                cwd=ROOT / "backend",
                env=env,
            )
        )

        print("[demo] 고객 앱(app-web) 기동…")
        procs.append(subprocess.Popen([npm_cmd(), "run", "dev"], cwd=ROOT / "app-web", env=env))

        print("[demo] Cloudflare 터널 여는 중… (주소가 나오기까지 5~10초)")
        tunnel = subprocess.Popen(
            [cloudflared, "tunnel", "--url", f"http://localhost:{APP_PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        procs.append(tunnel)

        watcher = threading.Thread(target=relay, args=(tunnel, "tunnel"), daemon=True)
        watcher.start()
        tunnel.wait()
    except KeyboardInterrupt:
        print("\n[demo] 종료 중… 공개 주소가 사라진다.")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
