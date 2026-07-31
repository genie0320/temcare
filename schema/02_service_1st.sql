-- ============================================================
-- 올라케어 · 1차 서비스 스키마 (회원 · 동의 · 법정 · 운영 · 한의원)
-- 콘텐츠 마스터(01_content_master.sql)에 이어서 실행
--
-- 원칙
--  1) 보류 기능(트래커·무드·케어포인트)의 테이블은 만들지 않는다.
--  2) audit_log / access_log 는 화면 기능이 아니라 데이터 접근 계층의 산출물이다.
--  3) 건강정보·문진응답은 민감정보 — 별도 동의 + 보유기간 정책 대상.
--  4) SQLite 문법 기준(프로토타입과 동일). 실 DB(PostgreSQL 등)로 옮길 때
--     TEXT PK → UUID, datetime('now') → now() 등만 치환하면 된다.
--     ★ 주의: PostgreSQL에서 `user` 는 예약어다. `app_user` 등으로 개명하거나
--       항상 따옴표로 감쌀 것. 이 파일은 SQLite 기준이라 그대로 두었다.
-- ============================================================

PRAGMA foreign_keys = ON;

-- ── 회원 ─────────────────────────────────────────────────────
CREATE TABLE user (
  id            TEXT PRIMARY KEY,
  nickname      TEXT,
  email         TEXT,                                  -- 소셜에서 수신(있을 때만)
  status        TEXT NOT NULL DEFAULT '정상',           -- 정상|휴면|제재|탈퇴예정|탈퇴
  joined_at     TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  last_login_at TEXT,
  dormant_at    TEXT,                                  -- 휴면 전환 시각
  withdraw_at   TEXT,                                  -- 탈퇴 요청 시각(유예 시작)
  purge_due_at  TEXT,                                  -- 분리보관 만료 = 파기 예정일
  app_version   TEXT,                                  -- CS 대응용
  device        TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE user_social (                             -- 소셜 로그인 연동
  user_id   TEXT NOT NULL REFERENCES user(id) ON DELETE CASCADE,
  provider  TEXT NOT NULL,                             -- kakao | google | apple ...
  social_id TEXT NOT NULL,
  linked_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  PRIMARY KEY (provider, social_id)
);
CREATE INDEX idx_user_social_user ON user_social(user_id);

CREATE TABLE user_status_log (                         -- 상태 전환 이력(사유·실행자 필수)
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    TEXT NOT NULL REFERENCES user(id) ON DELETE CASCADE,
  from_status TEXT,
  to_status  TEXT NOT NULL,
  reason     TEXT,
  actor      TEXT,                                     -- admin_account.id 또는 'system'
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ── 진단 결과 ────────────────────────────────────────────────
-- ★ 문진 응답은 민감정보. 원문 보관이 꼭 필요한지 검토 후 결정할 것(📌).
--   1차는 결과값만 보관하는 쪽을 기본으로 한다.
CREATE TABLE diagnosis_result (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT NOT NULL REFERENCES user(id) ON DELETE CASCADE,
  type_id     TEXT REFERENCES tem_type(id) ON DELETE SET NULL,
  raw_value   INTEGER,                                 -- 외부에서 받은 1~64 정수
  provider    TEXT NOT NULL DEFAULT 'mock',            -- mock | junchart
  status      TEXT NOT NULL DEFAULT '완료',             -- 대기|완료|실패|타임아웃
  error_code  TEXT,
  latency_ms  INTEGER,
  created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_diag_user ON diagnosis_result(user_id, created_at DESC);

-- ── 진단 결과 분포 통계 (익명 — 개인정보 아님) ────────────────
-- ★ user_id·IP·정확한 시각 등 식별자를 절대 넣지 않는다. '체질별 하루 카운트'만
--   누적하는 순수 집계 테이블이라 동의 없이 저장해도 된다(개인정보보호법상 익명정보).
--   가입 여부와 무관하게 판별 완료 시점에 +1 한다 — 문진만 하고 이탈한 사람도 포함해야
--   설문 편향 여부를 제대로 볼 수 있다. 목적: 준차트 연동 후 문항 편향 모니터링.
CREATE TABLE diagnosis_stat (
  type_id  TEXT NOT NULL REFERENCES tem_type(id) ON DELETE CASCADE,
  day      TEXT NOT NULL,                              -- 'YYYY-MM-DD'
  count    INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (type_id, day)
);

-- ── 약관 · 동의 ──────────────────────────────────────────────
CREATE TABLE terms_document (
  id    TEXT PRIMARY KEY,                              -- tos | privacy | marketing ...
  name  TEXT NOT NULL,
  sort  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE terms_version (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id  TEXT NOT NULL REFERENCES terms_document(id) ON DELETE CASCADE,
  version      TEXT NOT NULL,                          -- 'v3.2'
  body         TEXT NOT NULL,                          -- ★원문 스냅샷. 동의 시점 문안 보존
  effective_at TEXT NOT NULL,                          -- 시행일(예약 게시)
  is_major     INTEGER NOT NULL DEFAULT 0,             -- 중대 변경 → 재동의 필요
  status       TEXT NOT NULL DEFAULT '초안',            -- 초안|예약|게시|폐기
  created_at   TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  updated_by   TEXT
);
CREATE UNIQUE INDEX idx_terms_ver ON terms_version(document_id, version);

CREATE TABLE consent_item (                            -- 동의 '항목' 정의 (adm_038)
  id           TEXT PRIMARY KEY,                       -- tos | privacy | sensitive | age14 | mkt_push ...
  name         TEXT NOT NULL,
  required     INTEGER NOT NULL DEFAULT 1,             -- 1=필수 0=선택
  is_sensitive INTEGER NOT NULL DEFAULT 0,             -- ★민감정보 별도 동의 플래그
  channel      TEXT,                                   -- 마케팅 전용: push | sms | email
  document_id  TEXT REFERENCES terms_document(id) ON DELETE SET NULL,
  description  TEXT,
  sort         INTEGER NOT NULL DEFAULT 0,
  status       TEXT NOT NULL DEFAULT '게시'
);

CREATE TABLE user_consent (                            -- 동의 '이력' (adm_016). append-only
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT NOT NULL REFERENCES user(id) ON DELETE CASCADE,
  item_id     TEXT NOT NULL REFERENCES consent_item(id),
  version_id  INTEGER REFERENCES terms_version(id),    -- 동의 당시 약관 버전
  agreed      INTEGER NOT NULL,                        -- 1=동의 0=철회
  ip          TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_consent_user ON user_consent(user_id, item_id, created_at DESC);

-- ── 정보주체 권리요청 (adm_029 · 처리방침 제9조) ──────────────
-- ★원칙 10일 이내 처리 의무. due_at 기준 기한 알림 필수.
CREATE TABLE rights_request (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT REFERENCES user(id) ON DELETE SET NULL,
  kind        TEXT NOT NULL,                           -- 열람|정정|삭제|처리정지|동의철회
  channel     TEXT NOT NULL DEFAULT '앱',               -- 앱|이메일|유선
  body        TEXT,
  status      TEXT NOT NULL DEFAULT '접수',             -- 접수|본인확인|처리중|완료|거절
  reject_code TEXT,                                    -- 법정 거절 사유 코드
  assignee    TEXT,                                    -- admin_account.id
  received_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  due_at      TEXT NOT NULL,                           -- 접수 + 10일
  closed_at   TEXT
);
CREATE INDEX idx_rights_status ON rights_request(status, due_at);

CREATE TABLE rights_request_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES rights_request(id) ON DELETE CASCADE,
  step       TEXT NOT NULL,                            -- 본인확인|처리|회신|거절
  memo       TEXT,
  actor      TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ── 파기 (adm_030 · 처리방침 제8조) ──────────────────────────
CREATE TABLE retention_policy (                        -- 항목별 보유기간 정의
  id           TEXT PRIMARY KEY,                       -- user_withdrawn | inquiry | access_log ...
  name         TEXT NOT NULL,
  target_table TEXT NOT NULL,
  period_days  INTEGER NOT NULL,
  basis        TEXT,                                   -- 법적 근거(전자상거래법 등)
  status       TEXT NOT NULL DEFAULT '적용'
);

CREATE TABLE purge_log (                               -- 파기 이력
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  policy_id   TEXT REFERENCES retention_policy(id),
  target_table TEXT NOT NULL,
  row_count   INTEGER NOT NULL,
  method      TEXT NOT NULL DEFAULT '완전삭제',          -- 완전삭제|비식별화
  actor       TEXT,                                    -- 'system'(배치) 또는 admin id
  executed_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ── 운영자 계정 · 권한 (adm_021) ─────────────────────────────
CREATE TABLE admin_account (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role_id       TEXT NOT NULL REFERENCES admin_role(id),
  mfa_enabled   INTEGER NOT NULL DEFAULT 0,
  allow_ip      TEXT,                                  -- 콤마 구분 화이트리스트(선택)
  status        TEXT NOT NULL DEFAULT '활성',           -- 활성|잠금|비활성
  last_login_at TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE admin_role (
  id   TEXT PRIMARY KEY,                               -- super | director | editor | cs | viewer
  name TEXT NOT NULL,
  sort INTEGER NOT NULL DEFAULT 0
);

-- ★ 개인정보 열람(pii_read)은 콘텐츠 편집과 반드시 분리된 권한으로 둔다.
CREATE TABLE admin_permission (
  role_id  TEXT NOT NULL REFERENCES admin_role(id) ON DELETE CASCADE,
  resource TEXT NOT NULL,                              -- 화면ID(adm_015) 또는 리소스명
  action   TEXT NOT NULL,                              -- read|write|delete|publish|pii_read
  allowed  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (role_id, resource, action)
);

CREATE TABLE admin_login_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id TEXT,
  email      TEXT,
  success    INTEGER NOT NULL,
  ip         TEXT,
  user_agent TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ── 감사로그 · 접속기록 (adm_028) ★1일차 필수 ────────────────
-- 보관: audit_log 1년 이상 / access_log 2년 이상(민감정보 처리).
-- 두 테이블 모두 애플리케이션에서 UPDATE·DELETE 하지 않는다(append-only).
CREATE TABLE audit_log (                               -- 데이터 변경 이력
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id     TEXT,                                   -- admin_account.id | user.id | 'system'
  actor_type   TEXT NOT NULL DEFAULT 'admin',
  ip           TEXT,
  action       TEXT NOT NULL,                          -- create|update|delete|publish|export
  target_table TEXT NOT NULL,
  target_id    TEXT,
  before_json  TEXT,
  after_json   TEXT,
  created_at   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_audit_target ON audit_log(target_table, target_id, created_at DESC);
CREATE INDEX idx_audit_actor  ON audit_log(actor_id, created_at DESC);

CREATE TABLE access_log (                              -- 개인정보 열람 이력
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id    TEXT NOT NULL,
  ip          TEXT,
  target_user TEXT,                                    -- 열람 대상 회원
  fields      TEXT,                                    -- 열람 항목(건강정보 등)
  purpose     TEXT,                                    -- ★열람 사유(입력 강제)
  created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_access_target ON access_log(target_user, created_at DESC);

CREATE TABLE audit_review (                            -- 월 1회 이상 점검 기록(법정)
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  period     TEXT NOT NULL,                            -- 'YYYY-MM'
  reviewer   TEXT NOT NULL,
  finding    TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ── 고객지원 (adm_018 · adm_019) ─────────────────────────────
CREATE TABLE inquiry (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT REFERENCES user(id) ON DELETE SET NULL,
  kind        TEXT NOT NULL DEFAULT '일반',
  title       TEXT,
  body        TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT '접수',             -- 접수|처리중|완료
  assignee    TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  closed_at   TEXT
);

CREATE TABLE inquiry_reply (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  inquiry_id INTEGER NOT NULL REFERENCES inquiry(id) ON DELETE CASCADE,
  body       TEXT NOT NULL,
  actor      TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE notice (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  title      TEXT NOT NULL,
  body       TEXT,
  pinned     INTEGER NOT NULL DEFAULT 0,
  publish_at TEXT,                                     -- 예약 게시
  status     TEXT NOT NULL DEFAULT '초안',
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  updated_by TEXT
);

-- ── 협력 한의원 (adm_040) ★깔때기 출구 ───────────────────────
CREATE TABLE clinic (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,                           -- 한의원명
  director    TEXT,                                    -- 원장명
  sido        TEXT,                                    -- 시/도
  sigungu     TEXT,                                    -- 시/군/구
  address     TEXT,
  phone       TEXT,
  hours       TEXT,                                    -- 진료시간(자유 텍스트)
  intro       TEXT,                                    -- 한 줄 소개
  image       TEXT,
  map_url     TEXT,                                    -- 카카오/네이버 지도 링크(임베드 미사용)
  homepage    TEXT,
  status      TEXT NOT NULL DEFAULT '게시',
  sort        INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  updated_by  TEXT
);

-- ── 앱 설정 (adm_020) ────────────────────────────────────────
CREATE TABLE app_config (
  key         TEXT PRIMARY KEY,
  value       TEXT,
  description TEXT,
  updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  updated_by  TEXT
);
-- 예: diagnosis.provider = mock | junchart
--     maintenance.enabled / maintenance.message
--     app.min_version.ios / app.min_version.android

-- ============================================================
-- 2차 이후로 미룬 테이블 (지금 만들지 말 것)
--   push_campaign, push_log, notification      ← adm_031
--   faq, faq_feedback                          ← adm_032
--   banner, popup                              ← adm_033
--   media_asset                                ← adm_034
--   code_group, code_item                      ← adm_036
--   processor, third_party_provision           ← adm_037
--
-- 보류 (방향 확정 전까지 만들지 말 것 — 되돌릴 수 없는 기능)
--   daily_log(회원·날짜·축·값·출처)             ← 트래커. 구조만 확정됨
--   mood_log, point_rule, point_ledger
-- ============================================================
