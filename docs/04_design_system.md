# 디자인 시스템 (관리자)

> 프로토타입 `prototype/admin_prototype.html` 에서 추출. 실행하면 '시스템 → 디자인 시스템' 화면에서 전체 카탈로그를 볼 수 있다.

## 1. 색상 토큰

역할색은 계열+농도 스케일에서 파생한다. 컴포넌트는 **역할색만 참조**하고 원시 hex를 직접 쓰지 않는다.

```css
:root{
  /* 배경·표면 */
  --bg:#f4f6f8; --surface:#ffffff; --surface-2:#fafbfc;
  --border:#e4e8ec; --border-strong:#cdd4db;

  /* 텍스트 */
  --text:#1f2a33; --muted:#69747f; --faint:#9aa4ad;

  /* 주색 (그린) */
  --primary:#2f8f6b; --primary-dark:#256b52; --primary-soft:#e7f4ee;

  /* 강조 (오렌지) — 검수·주의 */
  --accent:#e08a3c; --accent-soft:#fbeede;

  /* 위험 (레드) — 삭제·오류 */
  --danger:#d15b52; --danger-soft:#fbe9e7;

  /* 정보 (블루) — 안내 노트 */
  --info:#3a6ea5; --info-soft:#e8f0f8;

  /* 사이드바 */
  --sidebar:#2e4053; --sidebar-2:#26374a; --sidebar-line:#3c5064;
  --sidebar-txt:#c3ccd6; --sidebar-active:#3aa37a;

  /* 형태 */
  --radius:10px; --radius-sm:7px;
  --shadow:0 1px 3px rgba(31,42,51,.06),0 1px 2px rgba(31,42,51,.04);

  /* 필터 폭 통일 */
  --filter-w:176px;
}
```

상태 색 매핑: 게시=`--primary` · 검수요청=`--accent` · 초안=`--faint` · 숨김/삭제=`--danger`

## 2. 타이포그래피

```
font-family: "Noto Sans KR", "Malgun Gothic", -apple-system, sans-serif;
```

황금비 기반 스케일. **최소 12px, 본문 15px.**

| 용도 | 크기 |
|---|---|
| 캡션·메타 | 12 |
| 보조 텍스트·힌트 | 13 |
| **본문 (기본)** | **15** |
| 소제목·카드 타이틀 | 18 |
| 페이지 타이틀 | 23 |

폼 컨트롤과 버튼은 13px, 리치 에디터 본문은 13.5px / line-height 1.75.

## 3. 컴포넌트 → React 매핑

프로토타입의 헬퍼 함수를 React 컴포넌트로 옮기는 대응표다. 이름을 그대로 쓰면 명세서·프로토타입과 대조하기 쉽다.

| 컴포넌트 | 프로토타입 헬퍼 | React |
|---|---|---|
| 목록 화면 전체 | `crudListHTML(CRUD[id])` | `<CrudList config>` |
| 필터바 | `crudFilterHTML()` | `<FilterBar filters>` |
| 목록 테이블 | `listTable(cols, rows)` | `<DataTable columns rows>` |
| 카드 | `.card` / `card2()` | `<Card title>` |
| 상세 레이아웃 | `detailWrap(main, side)` | `<DetailLayout main side>` |
| 게시 박스 | `sidePublish()` | `<PublishBox status onSave onDelete>` |
| 정보 카드 | `sideMeta()` | `<MetaPanel createdAt updatedAt updatedBy id>` |
| 사용처(역참조) | `sideUsageRows()` | `<UsagePanel rows>` |
| 도움말 | `sideTip()` | `<TipPanel>` |
| 폼 행 | `frow(label, control)` | `<FormRow label>` |
| 텍스트 입력 | `tin(id, value, placeholder)` | `<TextInput>` |
| 이미지 위젯 | `.imgdrop` | `<ImageField>` |
| 약점 다중선택 | 체크박스 그룹 | `<WeaknessPicker>` |
| 반복 카드 리스트 | `.wcard` + `.addbtn` | `<RepeatableCards>` |
| 실피커 모달 | 픽커 모달 | `<PickerModal source multiple>` |
| 안내 노트 | `.note` / `.note.warn` | `<Note tone>` |
| 상태 배지 | `.status-dot` | `<StatusBadge status>` |
| 칩 | `.pill` | `<Chip tone>` |

## 4. 이미지 위젯 규칙

- 썸네일 미리보기 + 기본(빈) 이미지 상태를 모두 가진다.
- **업로드 시 256px로 축소**한다(프로토타입 동작).
- 1차에서는 파일 스토리지에 저장하고 경로만 DB에 남긴다. 프로토타입은 base64 인라인이지만 **그 방식을 옮기지 말 것.**
- `alt` 텍스트 입력을 두면 접근성과 2차 미디어 라이브러리(adm_034) 준비가 동시에 된다.

## 5. 고객 화면 디자인 기준

`prototype/prescription_stream_mockup.html` 이 기준이다. 핵심 규칙:

- **크레센도**: 영양 → 식이 → 생활 → 약재로 내려가며 색이 진해진다. 잔잔하게 시작해 강하게 끝난다.
- **약재 = 끝판왕**: 어두운 그린 스포트라이트 + 👑 배지. 다른 정거장과 시각적 위계를 확실히 벌린다.
- **여정 스텝퍼**: 상단에 4정거장, 세로 스트림 라인으로 연결.
- **그룹 제목은 캐치프레이즈**: "'똥 막힌 하수도'를 위한 한약재" 같은 감성 별칭(`weakness.catchphrase`)을 쓴다.
- 결과화면(판정)과 처방화면(행동)은 **결을 나눈다.** 결과는 차분하게, 처방은 행동을 부른다.
