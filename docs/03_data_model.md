# 데이터 모델

> `schema/01_content_master.sql` (26테이블, 프로토타입 검증 완료) + `schema/02_service_1st.sql` (23테이블, 1차 신규) = **49테이블**
> 둘 다 SQLite 기준으로 작성되어 있고 그대로 실행 검증했다. PostgreSQL로 옮길 때 `user`가 예약어라는 점만 주의.

## 1. 전체 지도

```
                    ┌──────────────┐
                    │   weakness   │  ← 모든 콘텐츠 연결의 축 (10개)
                    │  약점 / IDEA  │     catchphrase = 고객 처방 그룹 제목
                    └──────┬───────┘
        ┌──────────┬───────┼────────┬──────────┬──────────┐
        │          │       │        │          │          │
   nutrient_    herb_    food   article    health_    illness
   card_w      card_w    _w      _w         sign_w      _w
        │          │       │        │          │          │
   nutrient_   herb_    food   article   health_sign  illness
     card       card              (+food/point/product)
        │          │
   nutrient      herb                    point ──┐  product ──┐
                                                 └── article ─┘

   ┌──────────┐         ┌────────────────────┐
   │ tem_type │────────▶│ tem_type_weakness  │──▶ weakness
   │ (64체질)  │────────▶│ tem_type_illness   │──▶ illness  (+pct)
   └──────────┘────────▶│ tem_type_curation  │──▶ 카드 id / food id
                        └────────────────────┘
```

**핵심**: 고객 처방 화면의 내용은 `tem_type → tem_type_weakness → weakness → *_weakness → 콘텐츠` 경로로 **자동 조회**된다. `tem_type_curation`은 영양·약재·식품군의 체질별 노출 선택을 담는 **예외 경로**다.

## 2. 콘텐츠 마스터 (01_content_master.sql)

| 테이블 | 용도 | 관리자 |
|---|---|---|
| `weakness` | 약점/IDEA 10개. `catchphrase`(감성 별칭), 격언 | adm_003 |
| `tem_type` | 64체질. `body_min/max`(체형 5중단점 2점), `herb_title/desc` | adm_002 |
| `tem_type_weakness` / `_illness` / `_curation` | 체질의 약점·발병율(%)·노출 선택 | adm_002 |
| `nutrient` + `nutrient_card` + `_weakness` | 영양소 + (영양소×관점) 카드 | adm_022 |
| `herb` + `herb_card` + `_weakness` | 약재 + (약재×효능기전) 카드 | adm_023 |
| `food` + `food_weakness` | 식품. `polarity`(권장/제한), `component`(핵심성분) | adm_025 |
| `point` + `point_weakness` | 혈자리. `image`, `video` | adm_026 |
| `article` + `article_weakness` | 요법관리. `kind`(식이/지압·마사지/생활/뜸) | adm_024 |
| `article_food` / `_point` / `_product` | 요법의 참고정보 연결 | adm_024 |
| `health_sign` + `_weakness` | 건강신호 | adm_007a |
| `illness` + `_weakness` | 예측질환. `image`, `description` | adm_007b |
| `product` | 제품. 외부몰 `url`만(결제 없음) | adm_027 |

**주의할 점**

- **카드 단위 = (항목 × 관점)** 이고 약점은 카드에 n:m으로 붙는다. 약점당 카드 1개가 아니다.
- `tem_type_curation.ref_id`는 영양·약재의 경우 **카드 id**(`nutrient_card.id` / `herb_card.id`), 식품군만 `food.id`다.
- 식이 권장/제한은 `article`이 아니라 **`food.polarity`** 가 결정한다.
- `point.tip`은 컬럼만 남아 있고 UI에서는 쓰지 않는다. `illness.category`도 같다.
- 모든 마스터에 `status` / `sort` / `created_at` / `updated_at` / `updated_by`가 있다.
- **FK cascade 주의**: 프로토타입에서 `db.export()`가 `PRAGMA foreign_keys`를 OFF로 리셋하는 버그가 있었다. 실 DB에서는 FK 제약이 항상 켜져 있는지 확인할 것.

## 3. 서비스 테이블 (02_service_1st.sql)

| 영역 | 테이블 | 비고 |
|---|---|---|
| 회원 | `user`, `user_social`, `user_status_log` | 상태 전환은 사유·실행자 필수 |
| 진단 | `diagnosis_result` | `raw_value`(1~64), `provider`(mock/junchart) |
| 진단 | `diagnosis_stat` | **익명 집계.** `type_id`+`day`별 카운트만. user_id/IP 없음 — 개인정보 아님. 설문 편향 분석용(2026-07-31 추가) |
| 약관·동의 | `terms_document`, `terms_version`, `consent_item`, `user_consent` | `terms_version.body` = **원문 스냅샷** |
| 권리요청 | `rights_request`, `rights_request_log` | `due_at` = 접수 + 10일 |
| 파기 | `retention_policy`, `purge_log` | 정책 값으로 배치가 돈다 |
| 운영자 | `admin_account`, `admin_role`, `admin_permission`, `admin_login_log` | `pii_read` 권한 분리 |
| **감사** | `audit_log`, `access_log`, `audit_review` | **append-only. 1일차 필수** |
| 고객지원 | `inquiry`, `inquiry_reply`, `notice` | |
| **한의원** | `clinic` | 깔때기 출구 |
| 설정 | `app_config` | `diagnosis.provider`, 점검 모드, 최소 버전 |

## 4. 만들지 않는 테이블

**2차** — `push_campaign` / `push_log` / `notification` / `faq` / `banner` / `media_asset` / `code_group` / `code_item` / `processor`

**보류(★테이블도 만들지 말 것)** — `daily_log` / `mood_log` / `point_rule` / `point_ledger`

보류 테이블을 미리 만들어 두지 않는 이유는 `docs/02_architecture_constraints.md` §5에 있다. 요약하면 **빈 테이블이 "곧 만들 것"이라는 신호가 되어 범위를 되살리기 때문**이다.

트래커 도입이 결정되면 구조는 이미 정해져 있다:

```sql
-- 도입 결정 시에만 생성할 것
CREATE TABLE daily_log (
  user_id TEXT, date TEXT, axis TEXT,   -- axis = 공통코드 (체온·수분·배변·기분)
  value TEXT, source TEXT,              -- source = 자가입력 | 자동수집
  PRIMARY KEY (user_id, date, axis)
);
```

축마다 컬럼을 만들지 않고 **세로로 쌓는다.** 축을 늘리거나 빼도 스키마를 안 건드린다.

## 5. 시드가 필요한 것

M0에서 넣어야 하는 최소 시드:

- `admin_role` (super / director / editor / cs / viewer) + `admin_permission` 매트릭스
- `admin_account` 최초 1건
- `terms_document` (tos / privacy / marketing) + 각 `terms_version` 1건
- `consent_item` — 이용약관 · 개인정보 수집이용 · **민감정보(별도)** · 만14세 확인 · 마케팅 수신(채널별)
- `retention_policy` — 탈퇴 분리보관 · 문의기록 · `access_log`(2년) · `audit_log`(1년+)
- `app_config` — `diagnosis.provider = mock`

콘텐츠 시드는 `prototype/ollacare.sqlite`에 더미가 들어 있다. 구조 확인용으로만 쓰고, 실데이터는 M6에서 넣는다.
