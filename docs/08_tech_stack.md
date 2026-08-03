# 기술 스택 · 개발 환경

> 원칙: **빠르게 구현하고 빠르게 확인한다.** 나중의 React Native 전환을 위해서는 "전환 시 오류를 줄이는" 최소한만 지불하고, "전환 비용을 0으로 만드는" 투자는 하지 않는다.

## 1. 확정 스택

| 영역 | 선택 | 이유 |
|---|---|---|
| 백엔드 | **Django + Django REST Framework** | 인증·세션·비밀번호 해싱·CSRF·마이그레이션이 검증된 상태로 들어 있다. 건강정보를 다루는 서비스에서 인증을 직접 조립하는 것이 가장 위험한 선택 |
| DB | **PostgreSQL** (관리형, **국내 리전**). **로컬 개발은 SQLite(결정: 2026-07-31, §6 참조)** | 국외 이전 시 처리방침에 국외이전 조항이 필요해진다. 국내 리전이면 그 항목이 통째로 사라진다. 로컬은 개발 컴퓨터 사양이 낮아(8GB RAM) Docker/PostgreSQL 상시 구동 부담을 줄이려는 선택 — CI가 PostgreSQL 호환성을 대신 지킨다 |
| 관리자 프론트 | **React + Vite + TypeScript** | 영구 웹. RN 전환 대상 아님 |
| 고객 프론트 | **React + Vite + TypeScript (모바일 웹)** | 1차는 앱 아님. 스토어 심사·강제 업데이트·푸시 인프라가 통째로 사라진다 |
| 스타일 | **Tailwind CSS + `tokens.ts` 단일 소스** | 가장 빠르게 화면을 만든다. 토큰만 RN으로 넘어가고 클래스는 버린다 — 의도된 선택 |
| 서버 상태 | **TanStack Query** | 캐싱·로딩·에러 처리를 직접 안 짜도 된다 |
| 클라 상태 | **Zustand** (필요한 만큼만) | 전역 상태는 최소로 |
| 라우팅 | **React Router** | |
| 테스트 | **pytest + pytest-django** · **Vitest + Testing Library**(app-web) | 프론트는 '단위 테스트'가 아니라 **화면 테스트**다 — 구현이 아니라 사용자에게 무엇이 보이는지만 본다(결정 #36). 검토에서 실제로 걸린 것(실패인데 '없음'으로 보이던 것)을 막으려고 2026-08-03에 추가했다 |
| 백엔드 패키지 관리 | **uv** (결정: 2026-07-31) | `pip`/`venv`보다 빠르고 `pyproject.toml`+lockfile로 재현 가능한 환경을 보장한다. `uv sync`, `uv run manage.py …` 형태로 사용 |

### Django Admin 방침

**Django Admin으로 관리자 화면을 만들지 않는다.** 목록·상세 3:1 사이드패널, 반복 카드, 실피커 모달, 큐레이션 2패널 규격(`docs/05_screen_conventions.md`)을 Django Admin으로 흉내내려 하면 커스터마이징 지옥이 된다. 관리자는 React SPA로 만들고 같은 DRF API를 쓴다.

단, Django Admin 자체는 **슈퍼유저 전용 + 접속 IP 제한**으로 켜 두는 것을 권한다. 긴급 데이터 수정 창구로 유용하고, 감사로그를 ORM 시그널에 걸어 두면 Admin에서 고친 것도 자동으로 기록된다.

**단, 개인정보(회원·동의·진단결과 등)는 Django Admin에 등록하지 않는다(결정: 2026-07-31).** `audit_log`(변경 이력)는 시그널로 자동으로 잡히지만, `access_log`(열람 이력)는 화면 코드에 명시적으로 넣는 방식이라 Django Admin의 기본 상세 페이지에서는 열람 기록이 남지 않는다. 건강정보를 다루는 서비스에서 "열람 기록이 안 남는 뒷문"을 만들 수는 없으므로, 이 비상 창구에는 **콘텐츠 마스터(영양·약재·식품 등 개인정보 아닌 것)만** 등록한다. `user` / `diagnosis_result` / `user_consent` / `rights_request` 등은 Admin에 아예 노출하지 않는다.

### Django Template을 쓰지 않는다

서버 렌더링 페이지는 만들지 않는다. 백엔드는 JSON API만 낸다.

## 2. 저장소 구조

단일 저장소 하나로 간다. 초기에 나누면 확인 속도만 느려진다.

```
olla-care/
├─ CLAUDE.md · README.md · docs/ · schema/ · spec/ · prototype/
├─ backend/                    # Django
│   ├─ config/                 # settings, urls, wsgi
│   └─ apps/
│       ├─ accounts/           # User, 소셜 연동, 세션, 상태 전환
│       ├─ consent/            # 약관·동의 항목·동의 이력
│       ├─ privacy/            # 권리요청, 파기, 보유기간
│       ├─ audit/              # audit_log, access_log  ← 다른 앱이 의존
│       ├─ content/            # 콘텐츠 마스터 전체(약점·체질·영양·약재·식품·혈자리·요법·건강신호·예측질환·제품)
│       ├─ clinic/             # 협력 한의원
│       ├─ diagnosis/          # 판별 어댑터, diagnosis_result
│       └─ support/            # 문의·공지·앱설정
├─ admin-web/                  # 관리자 React (RN 전환 대상 아님 — 제약 없음)
└─ app-web/                    # 고객 React (RN 전환 후보 — 아래 제약 적용)
    └─ src/
        ├─ core/               # ★플랫폼 무관: api 클라이언트 · 도메인 로직 · 타입 · 상태
        ├─ ui/                 # 웹 전용: 화면 · 컴포넌트 · 스타일
        └─ tokens.ts           # ★디자인 토큰 단일 소스 (Tailwind config가 여기서 생성됨)
```

## 3. 인증 — 세션 쿠키로 간다

토큰을 브라우저 저장소에 넣지 않는다. XSS 한 번이면 그대로 털린다.

- **고객**: 카카오 소셜 로그인 → 백엔드가 세션 쿠키 발급. `HttpOnly` · `Secure` · `SameSite=Lax`
  - **카카오 로그인은 서버 리다이렉트(OAuth authorization code) 방식으로 구현한다. JS SDK 팝업 방식은 쓰지 않는다(결정: 2026-07-31).** 카카오톡 공유 링크를 통해 인앱브라우저로 유입되는 게 주요 경로이고, 인앱브라우저는 팝업 기반 로그인이 막히는 경우가 있다.
  - **가입 시점은 문진 이후다.** 문진 → 결과 티저(비로그인) → 그 다음 로그인. 자세한 흐름은 `docs/02_architecture_constraints.md` §6.
- **운영자**: 이메일 + 비밀번호 → 같은 방식의 세션 쿠키. 2단계 인증은 2차
- 고객 웹과 API를 **같은 도메인**에서 서빙한다(리버스 프록시). CORS 설정이 필요 없어지고 쿠키 문제도 사라진다
- 관리자는 별도 서브도메인(`admin.…`)에 두고 쿠키 경로·이름을 분리한다

### ★ 스키마 조정 1건

`schema/02_service_1st.sql`은 `user`(고객)와 `admin_account`(운영자)를 별도 테이블로 두었다. Django에서는 **`AUTH_USER_MODEL`을 하나로 통합**하는 편이 훨씬 단순하고 안전하다.

```
accounts.User          ← AUTH_USER_MODEL. 고객·운영자 공용
                          is_staff=True 면 운영자
                          소셜 전용 계정은 set_unusable_password()
accounts.AdminProfile  ← User와 1:1. role · mfa_enabled · allow_ip
                          (기존 admin_account 테이블의 운영자 전용 컬럼)
```

이렇게 하면 인증 경로가 하나가 되고, 감사로그의 `actor`도 한 종류로 다룰 수 있다. **마이그레이션 작성 시 이 형태로 반영할 것.** 나머지 테이블 구조는 SQL 그대로 간다.

## 4. 감사로그 구현 — 시그널 + 금지 규칙

`docs/02_architecture_constraints.md` §1의 구현 방법이다.

`apps/audit/`에서 대상 모델의 `post_save` / `post_delete` 시그널을 받아 `audit_log`에 기록한다. `actor`와 `ip`는 미들웨어가 스레드 로컬(또는 contextvar)에 심어 둔 요청 컨텍스트에서 읽는다.

### ★ 반드시 지킬 금지 규칙

**아래 네 가지는 ORM 시그널이 발생하지 않는다. 감사로그에 구멍이 생기므로 금지한다.**

- `QuerySet.update()`
- `QuerySet.delete()` (개별 `instance.delete()`는 시그널이 뜬다)
- `bulk_create()` / `bulk_update()`
- 원시 SQL (`raw()`, `cursor.execute()`)

배치 처리가 꼭 필요하면 `apps/audit/`에 명시적으로 감사 기록을 남기는 전용 함수를 만들어 그것만 쓴다. CI에 이 패턴을 잡는 grep 검사를 넣는다.

개인정보 열람(`access_log`)은 시그널로 잡히지 않으므로, 회원 상세 조회 뷰에서 명시적으로 기록하고 **열람 사유 입력을 강제**한다.

## 5. 권한 — 기본 거부

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
```

새 엔드포인트는 **명시적으로 열어야만 열린다.** AI가 권한 선언을 깜빡해도 공개되지 않는다. 이것이 바이브코딩 최대 사고 유형(권한 검사 누락)에 대한 구조적 방어다.

**의도적인 예외 한 곳**: 문진(sc_009)·mock 판별(sc_009a)·결과 티저(sc_010)는 비로그인 상태로 동작해야 한다(`docs/02_architecture_constraints.md` §6). 이 엔드포인트들만 `permission_classes = [AllowAny]`로 **명시적으로** 선언한다. 다른 개인정보 API가 실수로 같이 열리지 않도록, 이 예외는 이 세 엔드포인트로 한정한다.

관리자 API는 `resource`(화면 ID)와 `action`(`read`/`write`/`delete`/`publish`/`pii_read`)을 뷰에 선언하고, 커스텀 퍼미션 클래스가 `admin_permission` 매트릭스를 조회해 판정한다. **`pii_read`는 독립 축이며 `write`가 있다고 따라오지 않는다.**

**시리얼라이저에 `fields = '__all__'` 금지.** 항상 화이트리스트로 적는다.

## 6. 빠르게 확인하는 환경 (이 절이 이 문서의 핵심)

목표: **`git clone` 후 명령 두 줄이면 시드 데이터가 든 화면이 뜬다.**

**로컬에 필요한 도구**: Python 3.12+, Node.js LTS, `uv`(백엔드 패키지 관리), `make`(개발 명령 실행). Docker·PostgreSQL 로컬 설치는 필요 없다(위 §1·아래 내용 참조). 2026-07-31 기준 `Genie-Blue`(8GB RAM) 환경에 Python 3.12.10 · Node 24.18.1 LTS · uv 0.11.32 · GNU Make 4.4.1(winget `ezwinports.make`)로 설치 확인함. Make 실행 로직은 OS별 셸 차이를 피하려고 `scripts/*.py`(순수 파이썬)에 있다 — Windows/Mac/Linux 어디서나 동일하게 동작한다.

**로컬 개발은 Docker를 쓰지 않는다(결정: 2026-07-31).** 개발 컴퓨터 사양이 낮은 경우(8GB RAM급)를 기준으로 잡는다 — Docker Desktop의 WSL2 백엔드는 그 자체로 1~2GB를 상시로 붙잡기 때문에, 저사양 환경에서는 이게 병목이 된다. 대신:

- **DB는 SQLite.** 별도 서버 프로세스 없이 파일 하나. 설치도 필요 없다(Python 내장).
- **PostgreSQL 호환성은 CI가 지킨다.** GitHub Actions에서 `pytest`를 실제 PostgreSQL(서비스 컨테이너, 깃허브 서버에서 도는 것이라 로컬 사양과 무관)로 돌려서, SQLite에서는 통과하지만 PostgreSQL에서는 깨지는 코드를 커밋 시점에 바로 잡는다. 이 CI가 있어야 이 조합이 안전하다 — §9 CI 체크리스트 참조.
- `DATABASE_URL` 환경변수로 백엔드를 전환한다: 로컬은 비워두면 SQLite 기본값, CI·배포는 PostgreSQL 연결 문자열.

```bash
make setup                    # 의존성 설치 + 마이그레이션 + 시드 (최초 1회, 언제든 다시 돌려도 안전)
make dev                      # 백엔드 + 관리자 화면 동시 기동 (Docker 없음)
make dev-app                  # 백엔드 + 고객 화면 동시 기동 — 관리자 대신 이걸 볼 때
```

필수로 갖출 것:

1. **컨테이너 없이 로컬에서 직접 띄운다.** 백엔드(Django)·프론트(Vite) 전부. 리로드 속도와 메모리 여유를 최우선으로 한다.
2. **`manage.py seed_demo`** — 프로토타입 `prototype/ollacare.sqlite`에서 콘텐츠 마스터를 읽어 넣고, 운영자 계정·약관·동의 항목·보유기간 정책·한의원 3곳까지 한 번에 채운다. 언제든 다시 돌릴 수 있게 멱등으로.
3. **mock 판별이 기본값** — `app_config['diagnosis.provider'] = mock`. 문진을 끝내면 즉시 결과가 나온다. **지연·실패·타임아웃을 쿼리 파라미터로 강제**할 수 있게 해서 sc_009a의 재시도 UI를 바로 확인한다.
4. **개발 전용 빠른 로그인** — 소셜 로그인 없이 테스트 계정으로 진입하는 경로. `DEBUG=True`에서만 열리게 하고 프로덕션 설정에서 물리적으로 차단한다. 영업 시연에도 유용하다.
5. **Vite dev proxy** — `/api`를 Django로 넘겨 같은 오리진처럼 개발한다. CORS를 만질 일이 없어진다.
6. **컴포넌트 카탈로그는 별도 도구 없이** — Storybook을 넣지 않는다. 관리자 안에 디자인 시스템 화면(adm_039)을 한 페이지로 두면 충분하다. 프로토타입에 이미 있다.
7. **시연용 시드 스위치** — 64체질 전부가 아니라 **콘텐츠가 채워진 대표 체질 3~5개**만 넣는 시드 옵션. 실데이터 입력(M6) 전에도 한의원 영업 시연이 가능해진다.
8. **저사양 환경 팁**: 관리자·고객 두 프론트를 동시에 띄우지 말고 지금 작업 중인 것만 켠다. `make dev`에 프론트 선택 옵션을 둔다(예: `make dev FRONT=admin`).

## 7. RN 전환 대비 — 딱 네 가지만

**고객 프론트(`app-web/`)에만 적용한다. 관리자는 전환 대상이 아니므로 아무 제약도 걸지 않는다.**

1. **`core/` 와 `ui/` 를 나눈다.** API 클라이언트·도메인 로직·타입·검증·상태는 `core/`에. 여기에 `import`가 웹 전용으로 새지 않게만 지킨다. 전환 비용의 대부분이 여기서 결정된다.
2. **`tokens.ts`가 디자인 토큰의 단일 소스.** 색·간격·타이포·반경을 JS 객체로 두고, `tailwind.config.js`가 그것을 읽어 생성되게 한다. CSS 변수에 직접 하드코딩하지 않는다. 토큰은 RN에 그대로 넘어간다.
3. **웹 전용 API는 얇은 어댑터 뒤에.** `localStorage` → `core/storage.ts` 하나면 충분하다. `window`·`document`를 화면 코드에서 직접 부르지 않는다.
4. **고객 화면 레이아웃은 flexbox 우선.** CSS Grid·`float`·`position: sticky`를 피한다. 꼭 필요하면 쓰되 주석으로 표시해 나중에 찾을 수 있게 한다. RN은 flexbox만 지원한다.

### 하지 않을 것 (전환 비용을 0으로 만들려는 투자)

- React Native for Web / Expo Web으로 시작하기
- 웹·RN 공용 컴포넌트 추상화 레이어 만들기
- 플랫폼 분기 코드(`Platform.select` 유사물) 미리 넣기
- 스타일을 RN 호환 객체로만 작성하기

이것들은 지금의 개발 속도를 확실히 깎는 대신 불확실한 미래를 산다. **전환은 UI 레이어 재작성으로 처리한다.** 그때는 명세서와 디자인 기준이 이미 있으므로 "설계 없는 재작성"이 아니다.

## 8. PWA

`manifest.json` + 아이콘 + 최소 서비스워커만 넣는다. 비용이 거의 없고 홈 화면에 추가하는 사용자에게 이득이다.

**기대는 하지 말 것.** iOS는 사용자가 직접 공유 → 홈 화면에 추가를 해야 하고 설치 유도 배너를 띄울 방법이 없다. 웹푸시도 그 조건에서만 동작한다. 1차는 푸시가 범위 밖이라 영향이 없다.

## 9. 보안 기본값 체크리스트

**설정**
- [x] `DEBUG=False`, `ALLOWED_HOSTS` 지정, `SECRET_KEY`는 환경변수
- [x] `SESSION_COOKIE_SECURE` · `CSRF_COOKIE_SECURE`
- [ ] `SECURE_SSL_REDIRECT` · `SECURE_HSTS_SECONDS` — **의도적으로 기본 False.** DEBUG=False일 때 자동으로 켰더니 CI 테스트가 301로 전부 실패했다(2026-07-31, nginx가 TLS를 종료하는 배포 구조와 안 맞음). 실제 배포에서 nginx의 `X-Forwarded-Proto`와 `SECURE_PROXY_SSL_HEADER`를 같이 설정할 때 켠다(§10-1). `check --deploy`는 이 상태에서 경고(W004/W008)만 내고 통과한다
- [x] `SESSION_COOKIE_HTTPONLY` · `SAMESITE=Lax`
- [x] `python manage.py check --deploy` 통과 (CI에서 매번 확인)
- [x] 시크릿은 코드·저장소에 없음 (`.env`는 `.gitignore`, gitleaks가 CI에서 추가 확인)

**코드**
- [x] `DEFAULT_PERMISSION_CLASSES = IsAuthenticated`
- [ ] 시리얼라이저에 `fields = '__all__'` 없음 — M1에서 실제 시리얼라이저가 생기면 확인
- [ ] 로그인·문진 제출에 요청 제한 (django-axes / django-ratelimit) — 아직 미설치
- [x] 감사로그 우회 4종(`update`/`bulk_*`/`raw`/queryset `delete`) 없음 — CI grep 검사
- [ ] 에러 응답에 스택트레이스·내부 경로 노출 없음 — DEBUG=False로 기본 방어되나 커스텀 에러 핸들러는 아직 없음

**CI (GitHub Actions)** — `.github/workflows/ci.yml` (2026-07-31 구축)
- [ ] `pytest` — 엔드포인트별 "권한 없으면 403" 테스트 포함. 지금은 로그인 필요 여부만 확인(§6 diagnosis 테스트) — 관리자 리소스별 403 테스트는 M1에서 추가
- [x] **`pytest`를 실제 PostgreSQL 서비스 컨테이너로도 실행** — 로컬 SQLite와의 동작 차이를 커밋 시점에 잡는다(§6)
- [x] `pip-audit` — 의존성 취약점
- [x] `bandit` — 파이썬 정적분석
- [x] `gitleaks` — 시크릿 유출
- [x] `manage.py check --deploy`
- [x] 감사로그 우회 패턴 grep 검사 — `backend/scripts/check_audit_bypass.sh`. `apps/audit/`는 검사 대상에서 제외(구현 자체이므로), 의도된 예외는 `# audit: intentional` 주석으로 표시

**오픈 전 1회**
- [ ] 자동 스캐너(OWASP ZAP 등) 1회
- [ ] 가능하면 외부 점검 — 건강정보라 사고 비용이 크다

## 10. 배포

### 10-0. 실사용자 받기 전까지는 정식 배포를 만들지 않는다 (결정: 2026-07-31)

트래커·무드를 "필요해지기 전엔 테이블도 안 만든다"고 한 것과 같은 논리다. **정식 배포 인프라(관리형 DB·오브젝트 스토리지·상시 서버)도 실사용자 가입을 받기 시작하는 시점 전까지는 미리 구축하지 않는다.**

- 그 전까지 개발·확인은 §6의 로컬 환경(`docker compose up` + `make dev`)으로 한다.
- 원장 등 외부에 시연이 필요할 때는 **ngrok / Cloudflare Tunnel 같은 무료 터널링**으로 로컬 개발 서버를 그 순간만 공개 HTTPS 주소로 노출한다. 포트포워딩·공인 IP 확보가 필요 없고(터널링 서비스로 나가는 연결이라 가정용 회선의 CGNAT 문제를 안 탄다), 시연이 끝나면 끄면 된다. 비용 0원.
- **개인 PC를 상시 서버로 쓰지 않는 이유**: ① 한국 가정용 회선은 대개 공인 IP가 없어(CGNAT) 상시 포트 개방 자체가 안 될 수 있다, ② 정전·재부팅·회선 장애에 대한 보장이 없어 "원장이 아무 때나 접속" 요건을 못 채운다, ③ 실사용자의 문진 응답(건강정보)이 전문적으로 관리되지 않는 개인 PC에 쌓이는 건 지금까지 설계한 감사로그·암호화·백업 체계와 정면으로 어긋난다.
- **전환 시점**: 실사용자 가입을 받기 시작하기 직전에 아래 정식 배포로 전환한다.

### 10-1. 정식 배포 (실사용자 유입 시점부터)

초기에는 단순하게. 앱 서버 1대 + 관리형 PostgreSQL + 오브젝트 스토리지(이미지) + 리버스 프록시면 충분하다.

- **후보: AWS Lightsail (서울 리전)** — 이미 보유 중인 인스턴스(1GB RAM·2vCPU·40GB SSD, 서울 A)가 있다. 다만 **DB는 이 인스턴스에 같이 넣지 않는다** — 1GB로는 nginx+Django+PostgreSQL을 함께 돌리기엔 여유가 없어 트래픽이 몰리는 순간(하필 시연 중) OOM으로 죽을 위험이 크다. 기존 인스턴스는 nginx+Django(도커)만 맡고, DB는 Lightsail Managed Database를 별도로 추가한다.
- 도커는 **배포용으로만** 쓴다. §6에서 정한 "개발 중엔 DB만 컨테이너"라는 원칙과 다른 층위의 얘기다 — 배포는 리로드 속도가 문제되지 않으므로 앱 전체를 컨테이너로 묶어도 된다.
- **국내 리전을 쓴다.** 개인정보 국외 이전이 없으면 처리방침 제7조를 "국외 이전하지 않음"으로 끝낼 수 있다
- DB는 **저장 시 암호화 + 자동 백업**을 켠다
- 로그는 접속기록 보관 요건(민감정보 2년)을 만족하는 보존 정책으로
- 스테이징 환경은 1차 범위 밖. 필요해지면 그때

## 11. 안 하는 것

Django Admin으로 관리자 만들기 · Django Template · JWT를 브라우저 저장소에 두기 · GraphQL · 마이크로서비스 · Storybook · Kubernetes · **프론트 단위 테스트**(컴포넌트 내부·훅 단위. 화면 테스트는 결정 #36으로 채택했으니 혼동하지 말 것) · React Native for Web · 스테이징 환경 · 관리자 프론트에 RN 전환 제약 걸기
