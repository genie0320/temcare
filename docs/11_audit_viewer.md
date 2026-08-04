# adm_028 감사로그·접속기록 화면 작업 계약

> 명세 정본: `spec/temcare_admin-screen-spec_v3.xlsx` — 시트1 `adm_028`(1차·P0·Super Admin 전용 **조회**), 시트2에 UI 요소 6개
> 이 문서는 **무엇을 만들고 무엇을 만들지 않을지의 계약**이다. 벗어나야 할 이유를 찾으면 진행하지 말고 먼저 물어볼 것.

## 1. 왜 지금 만드나

기록하는 쪽(`apps/audit/signals.py`)은 M1부터 돌고 있는데 **읽는 쪽이 없다.**
`apps/audit/views.py`는 Django 기본 스텁 그대로고 URL도 등록되지 않았다.
로그를 2년 보관하면서 **볼 방법이 없는 상태**다.

이 화면의 목적은 운영 기능이 아니라 **진단**이다 —
"지금 어느 테이블에 어떤 로그가 얼마나 남고 있나"를 눈으로 확인하는 것.
그래서 **로그를 가공하지 않고 원문 그대로 보여준다.**

## 2. ★ 먼저 확인할 것 — 이걸 빼면 화면이 통째로 안 열린다

`backend/apps/accounts/management/commands/seed_demo.py`의 `SUPER_RESOURCES`에
**`adm_028`이 없다.** 권한 매트릭스에 행이 없으면 `AdminResourcePermission`이
전부 거부한다 — 화면을 완성해도 **전원 403**이고, 원인을 찾기 매우 어렵다.

```python
SUPER_RESOURCES = [..., "adm_009", "adm_028"]   # ← 추가
EDITOR_RESOURCES = [...]                        # ← 넣지 않는다 (§4-2)
```

## 3. 만들 것

### 백엔드 — `apps/audit/`

| 엔드포인트 | 내용 | 권한 |
|---|---|---|
| `GET /api/audit/summary/` | **"얼만큼"** — 대상테이블 × 액션 건수, 최근 기록 시각, 전체 건수 | `adm_028` / `read` |
| `GET /api/audit/logs/` | `audit_log` 목록. 필터: 기간·행위자·액션·대상테이블. 페이지네이션 | `adm_028` / `read` |
| `GET /api/audit/logs/<id>/` | `before_json` / `after_json` **전문** | `adm_028` / `read` |
| `GET /api/audit/access-logs/` | `access_log` 목록 | `adm_028` / **`pii_read`** |

`apps/audit/urls.py`를 새로 만들고 `config/urls.py`에 `path("api/audit/", include(...))`로 건다.

`summary`가 사용자가 실제로 원한 것이다 — "어떤 부분에 어떤 로그가 얼마나 남고 있는지".
목록보다 이쪽을 먼저 만든다.

### 프론트 — `admin-web/src/pages/AuditLogPage.tsx`

탭 3개: **요약** / **데이터 변경**(audit_log) / **개인정보 열람**(access_log).

- 로그는 **원문 그대로** 보여준다. `before_json`/`after_json`은 `<pre>` + 등폭 글꼴.
  보기 좋게 가공하거나 요약하지 말 것 — 이 화면의 목적이 원문 확인이다.
- 행 클릭 → 상세에서 전/후 비교(시트2 요소4).
- 룩앤필은 `prototype/admin_prototype.html`과 기존 `*ListPage.tsx`를 따른다.

## 4. 반드시 지킬 것

1. **읽기 전용.** `ModelViewSet` 금지 — `ReadOnlyModelViewSet` 또는 GET만 있는 `APIView`.
   `audit_log`는 append-only다(`docs/02_architecture_constraints.md` §8). 쓰기 경로를
   만드는 순간 장부가 장부이기를 그만둔다. **삭제·편집 기능은 영원히 만들지 않는다.**

2. **`access_log`는 권한을 분리한다** — `required_action = "pii_read"`.
   `audit_log`는 `audit_secret_fields`로 이미 마스킹돼 있지만(#32),
   `access_log`에는 그런 장치가 없다. `target_user`(회원 식별자) · `fields`(열람 항목) ·
   `purpose`(사유)가 **원문 그대로** 들어 있다.
   → `CLAUDE.md` §2-1 "개인정보 열람 권한은 콘텐츠 편집 권한과 분리한다".
   `EDITOR_ACTIONS`에 `pii_read`가 없으므로 §2와 맞물려 이중으로 막힌다.

3. **목록 응답에 `before/after` 전문을 싣지 않는다.** 콘텐츠 본문이 통째로 들어 있어
   응답이 폭발한다. 목록은 잘라서(예: 200자 + `truncated: true`), 전문은 상세에서만.

4. **`PUBLIC_DEMO`에서 404로 막는다.**
   터널은 고객 앱(5173)만 열지만, 그 Vite proxy가 `/api`를 **같은 Django로 넘긴다**.
   즉 감사로그 API도 터널 너머에서 도달 가능하다. `dev-login`이 막혀 있어 로그인은
   못 하지만 문을 하나 더 잠근다 — `apps/accounts/views.py`의 `dev_login`과 같은 방식.

5. **화면에서 "불러오기 실패"와 "로그가 없음"을 같게 취급하지 않는다**(`CLAUDE.md` §5-1 #1).
   감사로그가 **비어 보이는 것**은 "안 쌓이고 있다"는 심각한 신호로 읽힌다. 실패를 빈
   목록으로 그리면 그 신호가 가짜로 뜬다. 실패는 실패라고 쓰고 재시도 문을 둔다.

6. 집계에 `.values()` / `.annotate()`는 써도 된다(읽기). 금지된 4종은 쓰기 계열이다.

## 5. 만들지 않을 것 (이번 범위 밖)

| 시트2 요소 | 처리 |
|---|---|
| 5. 월간 점검 확인 (`audit_review`) | **M4.** 법정 의무지만 이번 진단 화면의 목적이 아니다 |
| 6. CSV 내보내기 | **M4.** 내보내기는 그 자체가 `export` 감사 대상이라 설계가 따로 필요하다 |

## 6. ★ 에러 로그는 이번에 넣지 않는다 — 2단계로 분리

사용자가 "디버그를 위한 에러문구까지"를 요청했다. **같은 화면·같은 테이블에 넣지 말 것.**

| | `audit_log` | 에러 로그 |
|---|---|---|
| 무엇 | 누가 무엇을 바꿨나 | 서버가 어디서 터졌나 |
| 성격 | 법정 장부(2년 보관·append-only) | 개발 편의(휘발성 무방) |
| 양 | 하루 수십 건 | 하루 수천 건 가능 |

섞으면 ① 에러가 법정 기록을 덮고, ② **예외 메시지·스택트레이스에 요청 본문이 딸려
들어와 #32에서 마스킹한 개인정보가 그대로 다시 샌다.**

→ 2단계로: `config/settings.py`에 `LOGGING`을 새로 두고(현재 **아예 없다**) 파일에 남긴 뒤,
**`DEBUG`일 때만** 열리는 별도 화면에서 tail을 본다. 1단계를 끝내고 사용자에게 물어본 뒤 진행.

## 7. 물어볼 것 (임의로 정하지 말 것)

- **감사로그 화면에서 `access_log`를 조회한 것 자체를 `access_log`에 남길 것인가?**
  개인정보 열람이므로 남기는 것이 맞아 보이지만, 열람 사유 입력을 강제하면 진단용
  화면이 무거워진다. `record_access`는 아직 미구현이고 M4 예정이다.
- 보관 기간(감사로그 2년) 안내를 화면에 표시할지.

## 8. 검증 — 변이 테스트가 기준이다 (`CLAUDE.md` §5-2)

통과하는 테스트가 아니라 **지키는** 테스트여야 한다. 최소 이 셋을 일부러 망가뜨려 볼 것:

1. `permission_classes`를 지운다 → 로그인만 한 사람이 감사로그를 읽을 수 있으면 테스트 실패해야 한다.
2. `access-logs`의 `required_action`을 `pii_read` → `read`로 바꾼다 → **에디터가 개인정보
   열람 이력을 볼 수 있게 되므로 반드시 실패해야 한다.** 이게 이번 작업의 핵심 안전장치다.
3. `PUBLIC_DEMO` 차단을 지운다 → 실패해야 한다.

`make test`(백엔드 pytest + 프론트 vitest) · `make lint` 초록.
**커밋만 하지 말고 푸시까지** — 푸시 안 된 커밋 때문에 CI가 한 번 무력화된 적이 있다.
커밋은 사용자가 요청할 때만.

## 9. 다른 세션과의 충돌

지금 **원장 콘텐츠 입력 세션**이 병렬로 돌고 있다(`docs/10_content_import.md`).
그쪽은 `apps/content/`·`doctor_data/`를, 이쪽은 `apps/audit/`·`admin-web/`를 만지므로
대체로 겹치지 않는다. **단 `seed_demo.py`는 양쪽이 건드린다** — §2에서 이 파일을 수정하기
전에 `git status`로 확인하고, 충돌하면 덮어쓰지 말고 사용자에게 알릴 것.
