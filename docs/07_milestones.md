# 작업 순서 (마일스톤)

> 순서에 근거가 있다. 임의로 바꾸면 나중에 되돌아가야 하는 지점이 있다.

## 지금 상태 (세션 인수인계 — 2026-07-31 밤 업데이트, 체크포인트 5 완료)

**M0 완료 + M1 네 번째 화면(약재)까지 실동작.** 약점(adm_003) → 64유형(adm_002) → 영양소(adm_022)에 이어 약재(adm_023) 목록·상세 CRUD까지 브라우저에서 실데이터로 끝까지 확인됐다. 영양소에서 만든 `RepeatableCards`/`ImageField`/`WeaknessTagPicker`를 그대로 재사용해 백엔드·프론트 모두 거의 조립 수준으로 끝났다 — §C 패턴이 예상대로 재사용됨을 확인.

- **바로 이어서 할 일**: M1 순서대로 식품군(adm_025)부터. 식품군은 카드 구조가 아니라 **단일 레코드 + 약점 체크박스**(§B 패턴, 64유형과 비슷)라 `RepeatableCards`는 안 쓴다 — `ImageField`(resource="adm_025")·`WeaknessTagPicker`는 재사용. 극성(권장/제한) 배지·핵심성분 자동완성 필드가 새로 필요하다. 그다음은 혈자리(adm_026) → 건강신호(adm_007a) → 예측질환(adm_007b) → 제품(adm_027) → 요법관리(adm_024).
- **이번 세션에 한 일 (체크포인트 4 — 영양소)**:
  - `apps/content/serializers.py`·`views.py` — `NutrientViewSet`(목록/상세, `_sync_cards()`로 관점 카드를 "통째로 교체") + `NutrientPerspectiveOptionsView`(관점 자동완성 후보).
  - **대표 이미지 = 실제 파일 업로드로 구현**. 처음엔 `docs/08_tech_stack.md` §10-0만 보고 base64를 DB에 인라인으로 넣었다가, 사용자가 "파일을 선택할 수 있어야 하는데 링크 입력으로 바뀌었다"고 지적해 `docs/04_design_system.md` §4(파일 스토리지 + 경로만 DB, base64 금지)를 뒤늦게 확인하고 되돌렸다 — `docs/06_decisions.md` #20에 왜 두 문서를 다 봐야 했는지 기록해 둠. 최종 구현: `POST /api/content/image-upload/`(공통 엔드포인트, 화면마다 `resource` 파라미터로 권한 검사) → Django `default_storage`(로컬 `MEDIA_ROOT`) 저장 → URL만 CharField에 저장. 프론트는 파일 선택 → 캔버스 256px 축소 → 업로드 → 미리보기. Vite dev proxy에 `/media` 추가 필요(안 하면 업로드는 되는데 미리보기가 404남).
  - `admin-web/` — `NutrientListPage`/`NutrientDetailPage` + 새 컴포넌트 2종: `RepeatableCards`(§C 반복 카드 리스트), `ImageField`(파일 선택·리사이즈·업로드).
  - **로컬 개발 DB 유의사항 발견**: 화면에서 저장(통째로 교체)한 뒤 `seed_demo`를 재실행하면 카드가 중복될 수 있다 — 원인과 대처는 `docs/06_decisions.md` #21.
  - 프로토타입의 '디자인 시스템' 카탈로그를 `/system/design`(`DesignSystemPage.tsx`)으로 이식 — 정적 마크업이 아니라 **실제 컴포넌트를 그대로 불러와** 렌더링하는 살아있는 카탈로그다. 새 화면을 만들기 전엔 여기부터 볼 것(`docs/06_decisions.md` #22). 같이 발견·수정: CSS에서 빠져 있던 `.btn.xs`, 목록 화면 상태 열 폭이 화면마다 흔들리던 문제(`DataTable`에 `Column.width` 추가, `docs/05_screen_conventions.md` A-3-1).
- **이번 세션에 한 일 (체크포인트 5 — 약재)**: `HerbViewSet`/`HerbListSerializer`/`HerbDetailSerializer`/`HerbMechanismOptionsView` — 영양소와 완전히 동일한 구조(`_sync_cards`, "통째로 교체")에 `hanja`(한자/생약명) 필드만 추가. 프론트는 `HerbListPage`/`HerbDetailPage`가 `RepeatableCards`/`ImageField`/`WeaknessTagPicker`를 그대로 재사용 — 새 공통 컴포넌트를 하나도 안 만들었다(카드 필드명이 `mechanism`이라 `RepeatableCards`가 쓰는 `perspective` 모양으로 얇게 변환하는 어댑터만 `HerbDetailPage`에 둠).
- **테스트**: 백엔드 40개 통과(`pytest`, Herb 5개 추가), bandit·감사로그 우회 검사·`tsc -b`·`oxlint` 전부 클린. 브라우저로 두 화면(영양소·약재) 모두 목록→상세→저장→재조회 라운드트립 + 신규 생성 + 이미지 업로드 + 삭제(API 직접 확인) 확인함.
- **아직 안 한 것**: 식품군(adm_025)부터 나머지 6개 콘텐츠 화면, "권한 없는 접근이 감사로그에 남는가" 체크리스트(`docs/02_architecture_constraints.md` §2)는 여전히 TODO, `window.confirm` 삭제 흐름은 헤드리스 자동화로 검증 불가(수동 확인만 가능).
- **이 컴퓨터(`Genie-Blue`, 8GB RAM)에 설치된 도구**: Python 3.12 · Node.js LTS · uv · GNU Make(`ezwinports.make`) · GitHub CLI(`gh`, 인증됨) — 전부 winget으로 설치, PATH는 터미널 재시작해야 새로 인식됨(설치 직후만 해당)
- **로컬 개발 명령**: `make setup`(최초 1회) → `make dev`(관리자 화면) 또는 `make dev-app`(고객 화면). Docker 안 씀 — DB는 로컬 SQLite, PostgreSQL 호환은 CI가 검증(`docs/06_decisions.md` #16)
- 자세한 항목별 체크는 바로 아래 M0 목록의 ✅ 표시 참고. 결정 이력은 `docs/06_decisions.md`(현재 #17까지).

## M0 — 기반 (여기가 제일 중요하다)

**이 단계를 건너뛰면 나중에 전 코드를 다시 만져야 한다.**

0. **`docs/08_tech_stack.md`를 먼저 읽는다.** 스택·저장소 구조·인증 방식이 거기 정해져 있다. ✅
1. 프로젝트 스캐폴딩(Django+DRF / Vite×2), DB 연결(로컬 SQLite·CI/배포 PostgreSQL, §1·§6), 마이그레이션 ✅
   - `AUTH_USER_MODEL` 통합 형태로 반영(08 §3의 스키마 조정 1건) ✅
2. `schema/01_content_master.sql` + `schema/02_service_1st.sql` 적용 — ✅ **둘 다 완료.** 콘텐츠 마스터(01) 26테이블 전부 `apps/content/models.py`로 옮겨 마이그레이션 적용함
3. **감사로그·접속기록을 데이터 접근 계층에 심는다** (`docs/02_architecture_constraints.md` §1) — ✅ `AuditedModel` 상속 시 자동 기록(시그널). `access_log`는 M4(회원 상세 조회 화면)에서 채운다. 권한거부 로그는 여전히 TODO(아래 참고)
4. **권한 검사를 라우트 미들웨어에 심는다** (§2) — `pii_read` 분리 포함. ✅ `AdminResourcePermission`이 APIView·ViewSet 둘 다 지원하고 약점 CRUD로 실제 검증됨(`apps/content/tests.py`)
5. 관리자 로그인 + `admin_account` / `admin_role` / `admin_permission` 시드 — ✅ `seed_demo` + 실제 로그인 화면(`admin-web`)까지 동작
6. `DiagnosisProvider` 인터페이스 + `MockDiagnosisProvider` (§3) — ✅. 문진은 로그인 없이 시작(`docs/02_architecture_constraints.md` §6)

7. **빠른 확인 환경**(08 §6): `make setup` + `make dev`(또는 `make dev-app`) 두 줄로 시드 데이터가 든 화면이 뜨게 한다. `seed_demo` 멱등 ✅, mock 판별 기본값 ✅, Vite dev proxy ✅, 개발 전용 빠른 로그인 ✅(`/api/accounts/dev-login/`, DEBUG 전용).
8. **CI 안전장치**(08 §9): GitHub Actions에서 실제 PostgreSQL로 `pytest` + `pip-audit`/`bandit`/`gitleaks`/`check --deploy`/감사로그 우회 검사. ✅ (`.github/workflows/ci.yml`)

M0 완료 기준: **① `git clone` 후 명령 두 줄로 시드가 든 화면이 뜬다. ✅ ② 관리자로 로그인해 아무 레코드나 하나 수정하면 `audit_log`에 before/after가 남는다. ✅(자동 테스트로 증명, `apps/audit/tests.py`)**

**M0 완전히 끝났다.** "권한 없는 접근이 감사로그에 남는가"(§2 체크리스트)만 아직 TODO — `AuditLog.ACTION_CHOICES`에 거부(denied) 액션 개념이 없어서, 화면이 몇 개 더 붙어 패턴이 보이면 로그 형태를 같이 정하기로 미뤘다(`apps/accounts/permissions.py` 상단 주석 참고).

## M1 — 관리자 콘텐츠 마스터

프로토타입에 **이미 동작하는 구현이 있다.** 화면 구조·필드·상호작용을 그대로 옮기고 저장소만 실 DB로 바꾼다. 새로 설계할 것이 거의 없는 구간이다.

순서: ~~약점(adm_003)~~ ✅ → ~~64유형(adm_002)~~ ✅ → ~~영양소(adm_022)~~ ✅ → ~~약재(adm_023)~~ ✅ → 식품군(adm_025) → 혈자리(adm_026) → 건강신호(adm_007a) → 예측질환(adm_007b) → 제품(adm_027) → 요법관리(adm_024)

- 약점을 먼저 하는 이유: 모든 콘텐츠가 약점 태그로 연결되므로 이것이 없으면 나머지를 만들 수 없다.
- 64유형이 그다음인 이유: 큐레이션이 영양·약재 카드를 참조하므로, 카드가 생긴 뒤 큐레이션 부분만 나중에 채워도 된다.
- 공통 규격은 `docs/05_screen_conventions.md`(화면 구조)·`docs/04_design_system.md`(컴포넌트 매핑·이미지 위젯 규칙 등) 둘 다 — 화면 구현 전 둘 다 확인할 것(`docs/06_decisions.md` #20 — 하나만 보고 결정했다가 되돌린 사례). **첫 화면(약점)에서 공통 컴포넌트를 제대로 만들어 두면 나머지는 조립이다.** → 컴포넌트는 `admin-web/src/components/`에 있다(`DataTable`/`DetailLayout`/`PublishBox`/`MetaPanel`/`FormControls`/`StatusBadge`/`WeaknessTagPicker`/`PickerModal`/`CuratedPickList`/`RepeatableCards`/`ImageField`).
- 약재(adm_023)는 영양소와 거의 동일 구조였다(완료). 식품군(adm_025)은 다르다 — §C 반복 카드가 아니라 **단일 레코드 + 약점 체크박스**(§B, 64유형과 같은 패턴)다. `ImageField`(`resource="adm_025"`)·`WeaknessTagPicker`는 재사용하되 `RepeatableCards`는 쓰지 않는다.

## M2 — 고객 코어 플로우

> ★순서 변경(2026-07-31): **문진이 로그인보다 먼저다.** 근거는 `docs/06_decisions.md` #13, 세부 규칙은 `docs/02_architecture_constraints.md` §6.

1. 스플래시(sc_090)
2. 문진: 유도(sc_004a, 비로그인 진입 가능) → 설명(sc_008) → 진행(sc_009, 응답은 클라이언트에만 보관) → 대기(sc_009a)
   - 문항은 fixture, 판별은 mock. **비로그인 상태로 호출 가능한 mock 판별 엔드포인트**가 필요하다(`DEFAULT_PERMISSION_CLASSES`의 명시적 예외).
   - **실패·타임아웃 경로도 mock에서 재현**해 sc_009a의 재시도 UI를 검증한다.
3. 결과 티저: 1차 안내(sc_010, 비로그인) — 유형명/별명만 노출, '자세히 보기'가 로그인으로 이어진다.
4. 온보딩: 로그인(sc_091) → **약관 동의(sc_092)** → 접근권한 안내(sc_093)
   - sc_092가 이 마일스톤의 핵심이다. **민감정보 별도 동의 · 만 14세 확인 · 마케팅 수신 동의**를 여기서 받는다. 마케팅 동의는 발송 수단이 2차여도 **지금 받아둔다.**
   - 가입 완료 시점에 클라이언트가 들고 있던 문진 응답 + raw_value를 서버로 전송해 `diagnosis_result`를 생성한다.
5. 결과 상세: 결과 홈(sc_004b) → 건강신호(sc_005) → 예측질환(sc_006 + sc_006a 모달)
6. 홈(sc_101) — 1차는 축소 구성(인사말·체질 요약·문진 유도·처방 진입). 하단 탭은 **홈/더보기 2탭**으로 시작한다.

M2 완료 기준: **로그인 없이 문진을 끝내면 결과 티저가 뜨고, 거기서 가입하면 문진 응답이 저장되며 상세 결과가 보인다.**

## M3 — 처방 스트림 + 깔때기 출구 ★

**이 서비스의 가치가 전부 여기 있다.**

1. 처방 스트림 홈(sc_007) — 4정거장 스텝퍼, 세로 스트림, 캐치프레이즈 그룹 제목
2. ① 영양(sc_007a) → ② 식이(sc_007b) → ③ 생활(sc_007c) → ④ 약재(sc_007d)
3. **협력 한의원(sc_040)** + 관리자 한의원 마스터(adm_040)

- 데이터는 전부 **약점 태그 자동 조회**다(`docs/02_architecture_constraints.md` §6). 체질별 수동 큐레이션이 아니다.
- 디자인 기준은 `prototype/prescription_stream_mockup.html`. 크레센도와 약재 스포트라이트를 살릴 것.
- sc_007d 끝에서 sc_040으로 이어지는 CTA가 **깔때기의 전부**다. 여기를 대충 만들면 서비스 목적이 사라진다.

M3 완료 기준: **가입 → 문진 → 결과 → 처방 → 한의원 한 바퀴가 돈다. 1차의 실질적 완료 지점이다.**

## M4 — 법정 대응

M2에서 동의를 받기 시작했으므로 이 시점에는 반드시 있어야 한다.

- 관리자: 회원(adm_015) · 동의 이력(adm_016) · 동의 항목 정의(adm_038) · 약관(adm_017) · 권리요청(adm_029) · 파기(adm_030) · 감사로그 조회 화면(adm_028)
- 고객: 이용약관(sc_024) · 개인정보처리방침(sc_025) · 회원탈퇴(sc_029) · **권리요청(sc_030)** · **동의 관리(sc_031)**

`retention_policy` 값과 처리방침 문안이 어긋나지 않는지 대조할 것.

## M5 — 운영 최소

- 더보기(sc_023) · 문의(sc_026) · 공지(sc_027) · 버전정보(sc_028) · 공통 오류(sc_098)
- 관리자: 고객센터(adm_018) · 공지(adm_019) · 앱설정(adm_020) · 게시 관리(adm_010) · 대시보드(adm_001)

## M6 — 콘텐츠 입력

**여기서 처음으로 실데이터를 넣는다.** 64체질 × 약점 × 콘텐츠. 분량이 크므로 M1이 끝나는 대로 개발과 병행해도 된다.

우선순위 근거가 없으면 대표 체질 몇 개만 먼저 채워 시연용으로 쓰고, 나머지는 순차로 채운다.

---

## 하지 않는 것

- 트래커·무드·케어포인트 — **테이블도 만들지 않는다**
- 템라이프 독립 피드(sc_001~003) — 2차
- 푸시 발송·알림함 — 2차 (동의만 1차에서 수집)
- 광고 — 2차
- FAQ·문의 내역·재동의 모달·휴면·점검·강제업데이트 — 2차
- 문진 문항 CRUD·방제 관리 — 보류(외부 소관 또는 범위 밖)

## 막히면

- 명세서(`spec/*.xlsx`)에서 해당 화면 행을 먼저 읽는다. 시트2에 UI 요소가, 시트3에 변경 근거가 있다.
- 프로토타입을 브라우저로 열어 실제 동작을 확인한다.
- `📌` 표시가 붙은 항목은 **미확정**이다. 임의로 정하지 말고 물어본다.
- 명세서와 프로토타입이 어긋나면 **명세서가 우선**이다.
