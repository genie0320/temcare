# 올라케어 개발 편의 명령. docs/08_tech_stack.md §6 "빠르게 확인하는 환경".
# 실제 기동 로직은 scripts/*.py에 있다 — Make의 셸이 OS마다 달라서 생기는 문제를 피하려고.

.PHONY: setup dev dev-app demo test lint

setup:
	python scripts/setup.py

dev:
	python scripts/dev.py admin

dev-app:
	python scripts/dev.py app

# 시연용 공개 주소(Cloudflare Tunnel). 고객 앱만 열리고, 끝나면 Ctrl+C로 사라진다.
# 반드시 가짜 데이터로만 — docs/08_tech_stack.md §10-0.
demo:
	python scripts/demo.py

# 백엔드·프론트를 한 번에 돌린다. CI가 도는 것과 같은 것이라, 여기가 초록이면
# 다른 컴퓨터에서 작업해도 커밋 시점에 어긋나지 않는다.
test:
	cd backend && uv run pytest -q
	cd app-web && npm run test

lint:
	cd backend && uv run bandit -r apps config -x '*/migrations/*,*/tests.py,*/test_*.py' -q
	cd backend && bash scripts/check_audit_bypass.sh
	cd app-web && npx tsc -b && npx oxlint
	cd admin-web && npx tsc -b && npx oxlint
