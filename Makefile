# 올라케어 개발 편의 명령. docs/08_tech_stack.md §6 "빠르게 확인하는 환경".
# 실제 기동 로직은 scripts/*.py에 있다 — Make의 셸이 OS마다 달라서 생기는 문제를 피하려고.

.PHONY: setup dev dev-app test lint

setup:
	python scripts/setup.py

dev:
	python scripts/dev.py admin

dev-app:
	python scripts/dev.py app

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run bandit -r apps config -x '*/migrations/*,*/tests.py' -q
	cd backend && bash scripts/check_audit_bypass.sh
