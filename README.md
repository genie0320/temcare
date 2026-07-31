# 올라케어 — 클로드 코드 인수인계 패키지

2026-07-31 기준. 화면설계·데이터모델·범위 확정까지 끝난 상태에서 실구현으로 넘기기 위한 자료 묶음이다.

> **파일명은 전부 ASCII입니다.** 처음 배포본은 한글 파일명을 썼는데, zip에 UTF-8 플래그가 붙지 않아
> Windows 탐색기에서 압축을 풀 때 한글 이름 파일이 깨지거나 누락되는 문제가 있었습니다.
> 파일 내용과 문서 제목은 그대로 한글입니다. 아래 대응표를 참고하세요.
>
> | 파일 | 문서 제목 |
> |---|---|
> | `docs/01_scope_phase1.md` | 1차 개발 범위 (체크리스트) |
> | `docs/02_architecture_constraints.md` | 아키텍처 제약 — 나중에 못 고치는 것들 |
> | `docs/03_data_model.md` | 데이터 모델 |
> | `docs/04_design_system.md` | 디자인 시스템 (관리자) |
> | `docs/05_screen_conventions.md` | 공통 화면 규격 (관리자) |
> | `docs/06_decisions.md` | 왜 이렇게 되었나 — 구현에 영향을 주는 결정들 |
> | `docs/07_milestones.md` | 작업 순서 (마일스톤) |
> | `docs/08_tech_stack.md` | 기술 스택 · 개발 환경 |
> | `prototype/admin_prototype.html` | 올라케어 관리자 템플릿 |
> | `prototype/prescription_stream_mockup.html` | 처방 '내 몸을 아끼는 길' 목업 |

## 시작하는 법

1. 이 폴더를 새 저장소의 루트(또는 `docs/` 하위)에 둔다. `CLAUDE.md`는 **저장소 루트**에 있어야 세션 시작 시 자동으로 읽힌다.
2. `CLAUDE.md` → `docs/07_milestones.md` 순으로 읽는다.
3. `docs/08_tech_stack.md`로 스택과 개발 환경을 세우고, `docs/02_architecture_constraints.md`의 M0 항목부터 시작한다. **이 단계를 건너뛰면 나중에 전 코드를 다시 만져야 한다.**

## 구성

```
CLAUDE.md                          ← 최상위 컨텍스트. 세션마다 자동으로 읽힘
README.md                          ← 이 파일

docs/
  01_scope_phase1.md               ← 1차 화면 체크리스트 (관리자 25 · 고객 30)
  02_architecture_constraints.md   ← ★나중에 못 고치는 것들. 감사로그·권한·어댑터
  03_data_model.md                 ← 49테이블 지도와 주의점
  04_design_system.md              ← 색·타이포 토큰, React 컴포넌트 매핑
  05_screen_conventions.md         ← 목록/상세 템플릿, 반복카드, 피커, 큐레이션
  06_decisions.md                  ← 왜 이렇게 되었나. 되돌리지 않기 위해 알아야 할 것
  07_milestones.md                 ← M0~M6 마일스톤
  08_tech_stack.md                 ← ★스택·인증·감사로그 구현·빠른 확인 환경·보안 체크리스트

schema/
  01_content_master.sql            ← 콘텐츠 마스터 26테이블 (프로토타입 검증 완료)
  02_service_1st.sql               ← 회원·동의·법정·운영·한의원 23테이블 (1차 신규)

spec/
  temcare_admin-screen-spec_v3.xlsx     ← 관리자 41화면. `단계` 열로 필터
  temcare_customer-screen-spec_v5.xlsx  ← 고객 52화면. 동일

prototype/
  admin_prototype.html             ← ★관리자 화면의 동작·시각 기준. 브라우저로 바로 열림
  prescription_stream_mockup.html  ← ★고객 처방 스트림 디자인 기준
  ollacare.sqlite                  ← 콘텐츠 시드(더미)
```

## 프로토타입 사용법

`prototype/admin_prototype.html`을 **브라우저로 그냥 열면** 관리자 화면이 시드 데이터와 함께 실제로 동작한다. 서버도 인터넷도 설치도 필요 없다(sql.js를 인라인한 단일 파일). 편집한 내용은 IndexedDB에 자동 저장되고 `.sqlite` 파일로 내보낼 수 있다.

**참조 구현이지 이식 대상이 아니다.** 가져올 것은 화면 구조 · 필드 정의 · 상호작용 규칙 · 디자인 토큰이며, 이미 `docs/04`, `docs/05`에 추출해 두었다.

'시스템 → 디자인 시스템' 메뉴에 컴포넌트 카탈로그와 React 매핑표가 들어 있다.

## 명세서 사용법

`단계` 열을 `1차`로 필터링하면 그대로 작업 목록이 된다.

- 시트1 화면명세서: 목적 · 주요 UI 요소 · 데이터 소스 · 권한 · **단계** · 중요도 · 구현상태
- 시트2 UI요소: 화면별 요소 단위 정의. 상단 `공통-A`/`공통-B` 행은 전 화면 공통 규격
- 시트3 변경이력: 왜 그렇게 바뀌었는지. 되돌리려 할 때 먼저 읽을 것

`중요도`(P0~P2)와 `단계`(1차/2차/보류)는 **다른 축**이다. 법적으로 중요해도 지금 만들지 않는 것이 있다.

## 1차 완료 기준

mock 판별로 **가입 → 문진 → 결과 → 처방 → 협력 한의원 연결** 한 바퀴가 실제로 돈다.

완성도의 기준은 환자용이 아니라 **영업용**이다 — 원장이 다른 원장에게 "우리 앱이 이렇게 환자를 보냅니다"라고 시연할 수 있으면 1차는 끝이다.

## 절대 하지 말 것 (요약)

- 감사로그·권한을 나중으로 미루기 → **소급 부착 불가**
- 준차트를 직접 호출하는 코드를 어댑터 밖에 쓰기
- `단계 = 보류`인 기능의 테이블 미리 만들기
- 명세서에 없는 화면·필드를 임의로 추가하기
- `📌` 표시된 미확정 사항을 임의로 결정하기
- 감사로그를 우회하는 ORM 호출(`update`/`bulk_*`/`raw`/queryset `delete`) 쓰기
- Django Admin·Template으로 관리자 화면 만들기

## 원본 문서

전체 결정 이력, 갭 분석, 정합성 검토 원문은 claude.ai 프로젝트 **"TEM"** 에 있다.

- `claude/화면설계_결정로그.md` — 전체 결정 이력 (시간순)
- `claude/관리자_공통기능_갭분석.md` — 공통 관리자 기능 갭 분석
- `claude/고객화면_정합성검토_v2기준.md` — 고객↔관리자 정합성 검토
- `claude/1차범위_확정_2026-07-31.md` — 1차 범위 확정 근거
- `claude/개인정보처리방침_초안.md` — 처리방침 초안 (전 15조)
