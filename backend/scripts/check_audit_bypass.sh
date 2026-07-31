#!/usr/bin/env bash
# 감사로그 우회 4종 검사. docs/08_tech_stack.md §4, §9.
# QuerySet.update()/delete(), bulk_create()/bulk_update(), raw SQL은 ORM 시그널이
# 뜨지 않아 audit_log에 구멍이 생긴다 — CI에서 커밋마다 자동으로 잡는다.
set -euo pipefail
cd "$(dirname "$0")/.."

PATTERN='\.update\(|\.bulk_create\(|\.bulk_update\(|\.raw\(|cursor\.execute\('

MATCHES=$(grep -rnE "$PATTERN" apps --include='*.py' \
  | grep -v '/migrations/' \
  | grep -v 'tests\.py' \
  | grep -v '# audit: intentional' \
  | grep -v '^apps/audit/' \
  || true)

if [ -n "$MATCHES" ]; then
  echo "감사로그를 우회할 수 있는 패턴이 발견됐다:"
  echo "$MATCHES"
  echo ""
  echo "AuditedModel을 상속한 모델에는 QuerySet.update()/delete(), bulk_create/bulk_update, raw SQL을 쓰지 말 것."
  echo "정말 필요하면 apps/audit/service.py의 record()를 명시적으로 쓰고,"
  echo "감사 대상이 아닌 모델(예: 익명 집계)이라 의도된 것이면 그 줄 끝에 '# audit: intentional' 주석을 남길 것."
  exit 1
fi

echo "감사로그 우회 패턴 없음."
