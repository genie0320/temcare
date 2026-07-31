-- 올라케어 · 콘텐츠 마스터 스키마 (프로토타입 검증 완료)
-- 출처: 올라케어_관리자_템플릿.html / schema.js
-- 26 테이블 · 관리자 adm_002/003/007a/007b/022~027 대응
PRAGMA foreign_keys = ON;

-- 약점 / IDEA 마스터 -----------------------------------------
CREATE TABLE weakness (
  id       TEXT PRIMARY KEY,
  name     TEXT NOT NULL,
  wtype    TEXT NOT NULL DEFAULT '약점',      -- 약점 | IDEA
  catchphrase TEXT,                            -- 감성 별칭 (예: '똥 막힌 하수도') · 처방 그룹 제목에 사용
  speaker  TEXT,                               -- 격언 화자
  source   TEXT,                               -- 격언 출처
  aphorism TEXT,                               -- 격언
  status   TEXT NOT NULL DEFAULT '게시',
  sort     INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);

-- 체질(64유형) 마스터 ----------------------------------------
CREATE TABLE tem_type (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,                 -- 체질명 (TE-5 등)
  nickname      TEXT,                          -- 별명 (자유 텍스트)
  body_value    INTEGER NOT NULL DEFAULT 50,   -- (구) 단일값 · 보존
  body_min      INTEGER NOT NULL DEFAULT 40,   -- 체형특성 범위 시작(5중단점 인덱스)
  body_max      INTEGER NOT NULL DEFAULT 60,   -- 체형특성 범위 종료
  body_desc     TEXT,
  herb_title    TEXT,                          -- 인생처방·약재 섹션 제목(고객 화면 상단)
  herb_desc     TEXT,                          -- 인생처방·약재 섹션 설명
  status        TEXT NOT NULL DEFAULT '게시',
  sort          INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);
CREATE TABLE tem_type_weakness (          -- 체질 × 약점 (n:m)
  type_id     TEXT NOT NULL REFERENCES tem_type(id)  ON DELETE CASCADE,
  weakness_id TEXT NOT NULL REFERENCES weakness(id)  ON DELETE CASCADE,
  PRIMARY KEY (type_id, weakness_id)
);
CREATE TABLE tem_type_illness (           -- 체질별 예측질환 발병율(%)
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  type_id  TEXT NOT NULL REFERENCES tem_type(id) ON DELETE CASCADE,
  illness_id TEXT REFERENCES illness(id) ON DELETE SET NULL,
  pct      INTEGER NOT NULL DEFAULT 0,
  sort     INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE tem_type_curation (          -- 체질별 큐레이션(수동 노출 선택)
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  type_id  TEXT NOT NULL REFERENCES tem_type(id) ON DELETE CASCADE,
  kind     TEXT NOT NULL,                       -- nutrient | herb | food
  ref_id   TEXT NOT NULL,                       -- 대상 마스터의 id
  polarity TEXT,                                -- food 전용: 권장 | 제한
  sort     INTEGER NOT NULL DEFAULT 0
);

-- 영양소 마스터 + 약점별 관점 카드 ---------------------------
CREATE TABLE nutrient (
  id     TEXT PRIMARY KEY,
  name   TEXT NOT NULL,
  image  TEXT,
  status TEXT NOT NULL DEFAULT '게시',
  sort   INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);
CREATE TABLE nutrient_card (              -- 같은 영양소, 다른 관점
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  nutrient_id TEXT NOT NULL REFERENCES nutrient(id) ON DELETE CASCADE,
  perspective TEXT,                            -- 개선분야(관점)
  description TEXT,
  sort        INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE nutrient_card_weakness (
  card_id     INTEGER NOT NULL REFERENCES nutrient_card(id) ON DELETE CASCADE,
  weakness_id TEXT NOT NULL REFERENCES weakness(id) ON DELETE CASCADE,
  PRIMARY KEY (card_id, weakness_id)
);

-- 약재(인생처방) 마스터 + 약점별 효능 카드 -------------------
CREATE TABLE herb (
  id     TEXT PRIMARY KEY,
  name   TEXT NOT NULL,
  hanja  TEXT,
  image  TEXT,
  status TEXT NOT NULL DEFAULT '게시',
  sort   INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);
CREATE TABLE herb_card (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  herb_id   TEXT NOT NULL REFERENCES herb(id) ON DELETE CASCADE,
  mechanism TEXT,                              -- 효능 기전
  description TEXT,
  sort      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE herb_card_weakness (
  card_id     INTEGER NOT NULL REFERENCES herb_card(id) ON DELETE CASCADE,
  weakness_id TEXT NOT NULL REFERENCES weakness(id) ON DELETE CASCADE,
  PRIMARY KEY (card_id, weakness_id)
);

-- 식품군 마스터 ----------------------------------------------
CREATE TABLE food (
  id        TEXT PRIMARY KEY,
  polarity  TEXT NOT NULL DEFAULT '권장',       -- 권장 | 제한
  component TEXT,                               -- 핵심성분
  foods     TEXT,                               -- 식품 목록
  description TEXT,
  image     TEXT,                               -- 대표 이미지(선택)
  status    TEXT NOT NULL DEFAULT '게시',
  sort      INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);
CREATE TABLE food_weakness (
  food_id     TEXT NOT NULL REFERENCES food(id) ON DELETE CASCADE,
  weakness_id TEXT NOT NULL REFERENCES weakness(id) ON DELETE CASCADE,
  PRIMARY KEY (food_id, weakness_id)
);

-- 혈자리 마스터 ----------------------------------------------
CREATE TABLE point (
  id       TEXT PRIMARY KEY,
  name     TEXT NOT NULL,
  hanja    TEXT,
  description TEXT,
  location TEXT,
  tip      TEXT,
  image    TEXT,
  video    TEXT,
  status   TEXT NOT NULL DEFAULT '게시',
  sort     INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);
CREATE TABLE point_weakness (
  point_id    TEXT NOT NULL REFERENCES point(id) ON DELETE CASCADE,
  weakness_id TEXT NOT NULL REFERENCES weakness(id) ON DELETE CASCADE,
  PRIMARY KEY (point_id, weakness_id)
);

-- 체질별 관리법(아티클: 식이/지압/생활/뜸) -------------------
CREATE TABLE article (
  id     TEXT PRIMARY KEY,
  kind   TEXT NOT NULL DEFAULT '식이',          -- 식이 | 지압·마사지 | 생활 | 뜸
  title  TEXT NOT NULL,
  body   TEXT,                                  -- 본문(HTML)
  image  TEXT,
  video  TEXT,
  status TEXT NOT NULL DEFAULT '게시',
  sort   INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);
CREATE TABLE article_weakness (
  article_id  TEXT NOT NULL REFERENCES article(id) ON DELETE CASCADE,
  weakness_id TEXT NOT NULL REFERENCES weakness(id) ON DELETE CASCADE,
  PRIMARY KEY (article_id, weakness_id)
);

-- 건강신호 마스터 --------------------------------------------
CREATE TABLE health_sign (
  id     TEXT PRIMARY KEY,
  name   TEXT NOT NULL,
  note   TEXT,                                  -- 항목설명(관점/설명)
  image  TEXT,                                  -- 대표 이미지(선택)
  status TEXT NOT NULL DEFAULT '게시',
  sort   INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);
CREATE TABLE health_sign_weakness (
  sign_id     TEXT NOT NULL REFERENCES health_sign(id) ON DELETE CASCADE,
  weakness_id TEXT NOT NULL REFERENCES weakness(id) ON DELETE CASCADE,
  PRIMARY KEY (sign_id, weakness_id)
);

-- 예측질환 마스터 --------------------------------------------
CREATE TABLE illness (
  id       TEXT PRIMARY KEY,
  name     TEXT NOT NULL,
  category TEXT,                                -- 분류(보존 · 현재 UI 미노출)
  description TEXT,                             -- 항목설명(상세)
  image    TEXT,                               -- 대표 이미지(선택)
  status   TEXT NOT NULL DEFAULT '게시',
  sort     INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);
CREATE TABLE illness_weakness (
  illness_id  TEXT NOT NULL REFERENCES illness(id) ON DELETE CASCADE,
  weakness_id TEXT NOT NULL REFERENCES weakness(id) ON DELETE CASCADE,
  PRIMARY KEY (illness_id, weakness_id)
);

-- 제품 마스터 ------------------------------------------------
CREATE TABLE product (
  id     TEXT PRIMARY KEY,
  name   TEXT NOT NULL,                          -- 상품명
  description TEXT,                               -- 상품설명
  image  TEXT,                                    -- 상품이미지
  url    TEXT,                                    -- 연결 URL
  status TEXT NOT NULL DEFAULT '게시',
  sort   INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime')),
  updated_by TEXT DEFAULT '원장'
);

-- 관리법 ↔ 참고정보(식품군·혈자리·제품) 연결 --------------------
CREATE TABLE article_food (
  article_id TEXT NOT NULL REFERENCES article(id) ON DELETE CASCADE,
  food_id    TEXT NOT NULL REFERENCES food(id)    ON DELETE CASCADE,
  PRIMARY KEY (article_id, food_id)
);
CREATE TABLE article_point (
  article_id TEXT NOT NULL REFERENCES article(id) ON DELETE CASCADE,
  point_id   TEXT NOT NULL REFERENCES point(id)   ON DELETE CASCADE,
  PRIMARY KEY (article_id, point_id)
);
CREATE TABLE article_product (
  article_id TEXT NOT NULL REFERENCES article(id)  ON DELETE CASCADE,
  product_id TEXT NOT NULL REFERENCES product(id)  ON DELETE CASCADE,
  PRIMARY KEY (article_id, product_id)
);
