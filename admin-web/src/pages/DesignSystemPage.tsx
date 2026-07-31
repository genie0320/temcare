import { useState } from 'react'
import { Card } from '../components/DetailLayout'
import { FormRow, SegToggle, TextArea, TextInput } from '../components/FormControls'
import { ImageField } from '../components/ImageField'
import { PageHead } from '../components/PageHead'
import { MetaPanel } from '../components/MetaPanel'
import { PublishBox } from '../components/PublishBox'
import { DataTable, type Column } from '../components/DataTable'
import { RepeatableCards, type RepeatableCardItem } from '../components/RepeatableCards'
import { StatusBadge } from '../components/StatusBadge'
import { WeaknessTagPicker } from '../components/WeaknessTagPicker'
import type { ContentStatus } from '../types/weakness'

const COLOR_GROUPS: { name: string; tokens: [string, string][] }[] = [
  {
    name: '배경 · 표면 · 경계',
    tokens: [
      ['--bg', '#f4f6f8'],
      ['--surface', '#ffffff'],
      ['--surface-2', '#fafbfc'],
      ['--border', '#e4e8ec'],
      ['--border-strong', '#cdd4db'],
    ],
  },
  {
    name: '텍스트',
    tokens: [
      ['--text', '#1f2a33'],
      ['--muted', '#69747f'],
      ['--faint', '#9aa4ad'],
    ],
  },
  {
    name: '주요 Primary (그린)',
    tokens: [
      ['--primary', '#2f8f6b'],
      ['--primary-dark', '#256b52'],
      ['--primary-soft', '#e7f4ee'],
    ],
  },
  {
    name: '강조 Accent (오렌지) — 검수·주의',
    tokens: [
      ['--accent', '#e08a3c'],
      ['--accent-soft', '#fbeede'],
    ],
  },
  {
    name: '위험 Danger (레드) — 삭제·오류',
    tokens: [
      ['--danger', '#d15b52'],
      ['--danger-soft', '#fbe9e7'],
    ],
  },
  {
    name: '정보 Info (블루) — 안내 노트',
    tokens: [
      ['--info', '#3a6ea5'],
      ['--info-soft', '#e8f0f8'],
    ],
  },
]

interface DemoRow {
  id: string
  name: string
  tag: string
  status: ContentStatus
}

const DEMO_ROWS: DemoRow[] = [
  { id: 'NUT-02', name: '마그네슘', tag: '부종', status: '초안' },
  { id: 'NUT-01', name: '비타민 B-complex', tag: '추위', status: '게시' },
]

const REACT_MAP: [string, string][] = [
  ['목록 화면 전체', 'DataTable + PageHead + toolbar'],
  ['목록 테이블', '<DataTable columns rows rowKey onRowClick>'],
  ['카드', '<Card title sub right>'],
  ['상세 레이아웃', '<DetailLayout main side>'],
  ['게시 박스', '<PublishBox status onStatusChange onSave onDelete>'],
  ['정보 카드', '<MetaPanel id createdAt updatedAt updatedBy>'],
  ['폼 행', '<FormRow label required>'],
  ['텍스트 입력 / 여러 줄', '<TextInput> / <TextArea>'],
  ['세그먼트 토글', '<SegToggle value options onChange>'],
  ['이미지 위젯', '<ImageField value onChange resource>'],
  ['약점 다중선택 (칩)', '<WeaknessTagPicker selectedIds onChange>'],
  ['반복 카드 리스트 (§C)', '<RepeatableCards cards onChange fieldLabel>'],
  ['실피커 모달 (§D)', '<PickerModal title items selectedIds onApply onClose>'],
  ['체질 큐레이션 피커', '<CuratedPickList label ids weaknessIds candidatesPath onChange>'],
  ['예측질환 발병율 행', '<IllnessRateRows rows onChange>'],
  ['체형특성 5중단점 슬라이더', '<BodySlider lo hi onChange>'],
  ['상태 배지', '<StatusBadge status>'],
  ['페이지 헤더', '<PageHead title description backTo actions>'],
]

// prototype/admin_prototype.html의 'design-system' 화면(2021~2112행)을 옮긴 것.
// 정적 마크업을 베낀 게 아니라 실제로 화면에서 쓰는 컴포넌트를 그대로 불러와 렌더링한다 —
// 그래야 컴포넌트가 바뀌면 이 페이지도 같이 바뀌어서 카탈로그가 실물과 어긋나지 않는다.
export function DesignSystemPage() {
  const [seg, setSeg] = useState<'약점' | 'IDEA'>('약점')
  const [weaknessIds, setWeaknessIds] = useState<string[]>([])
  const [image, setImage] = useState('')
  const [cards, setCards] = useState<RepeatableCardItem[]>([
    { perspective: '대사회복', description: '샘플 카드 — RepeatableCards 데모', weakness_ids: [] },
  ])
  const [publishStatus, setPublishStatus] = useState<ContentStatus>('게시')

  const tableColumns: Column<DemoRow>[] = [
    { key: 'name', label: '이름', render: (r) => <><span className="name">{r.name}</span> <span className="muted">{r.id}</span></> },
    { key: 'tag', label: '태그', render: (r) => <span className="chip">{r.tag}</span> },
    { key: 'status', label: '상태', width: '80px', render: (r) => <StatusBadge status={r.status} /> },
  ]

  return (
    <>
      <PageHead
        title="디자인 시스템"
        description="관리자 전반에서 재사용하는 색·타이포·컴포넌트 카탈로그. 새 화면은 이 요소를 조합해 구성한다."
      />

      <div className="note">
        <span className="i">🎨</span>
        <div>
          이 화면은 <b>실제 컴포넌트를 그대로 불러와</b> 보여주는 살아있는 카탈로그다. 새 화면을 만들 때 여기 있는 것부터 재사용할 것 —
          없는 경우에만 새로 만들고, 만들었으면 이 페이지에도 추가한다.
        </div>
      </div>

      <Card title="색상 토큰" sub="CSS 변수 (:root) — docs/04_design_system.md §1">
        {COLOR_GROUPS.map((g) => (
          <div key={g.name} style={{ marginBottom: 16 }}>
            <div className="hint" style={{ marginBottom: 6, fontWeight: 600 }}>{g.name}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {g.tokens.map(([name, hex]) => (
                <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 32, height: 32, borderRadius: 8, border: '1px solid var(--border)', background: `var(${name})` }} />
                  <div style={{ fontSize: 12 }}>
                    <div style={{ fontWeight: 600 }}>{name}</div>
                    <div className="muted">{hex}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </Card>

      <Card title="타이포그래피" sub="최소 12px · 본문 15px — docs/04_design_system.md §2">
        <h1 style={{ marginBottom: 6 }}>제목 H1 · 23 / 700</h1>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>섹션 H2 · 18 / 700</h2>
        <p style={{ marginBottom: 4 }}>본문 텍스트 · 15 / 400</p>
        <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 4 }}>보조 텍스트 · 13 / muted</p>
        <div style={{ fontSize: 12, color: 'var(--faint)' }}>캡션(최소) · 12 / faint</div>
      </Card>

      <Card title="버튼">
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <button className="btn primary">주요</button>
          <button className="btn">기본</button>
          <button className="btn ghost">고스트</button>
          <button className="btn danger">삭제</button>
          <button className="btn primary sm">sm</button>
          <button className="btn xs">xs</button>
        </div>
      </Card>

      <Card title="칩 · 배지 · 상태">
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
          <span className="chip">약점 칩</span>
          <span className="chip idea">IDEA 칩</span>
          <span className="chip off">비활성</span>
          <span className="pill a">pill A</span>
          <span className="pill b">pill B</span>
          <span className="pill c">pill C</span>
        </div>
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          <StatusBadge status="게시" />
          <StatusBadge status="초안" />
          <StatusBadge status="숨김" />
        </div>
      </Card>

      <Card title="폼 컨트롤">
        <div className="form-grid" style={{ maxWidth: 560 }}>
          <FormRow label="텍스트 입력">
            <TextInput value="" onChange={() => {}} placeholder="예: 비타민 B-complex" />
          </FormRow>
          <FormRow label="여러 줄">
            <TextArea value="" onChange={() => {}} placeholder="설명 입력" />
          </FormRow>
          <FormRow label="세그먼트">
            <SegToggle value={seg} options={['약점', 'IDEA']} onChange={setSeg} />
          </FormRow>
          <FormRow label="약점 다중선택">
            <WeaknessTagPicker selectedIds={weaknessIds} onChange={setWeaknessIds} />
          </FormRow>
          <FormRow label="이미지 위젯">
            <ImageField value={image} onChange={setImage} resource="adm_022" />
          </FormRow>
        </div>
      </Card>

      <Card title="노트">
        <div className="note">
          <span className="i">ℹ</span>
          <div>정보 노트 (note)</div>
        </div>
        <div className="note warn">
          <span className="i">⚠</span>
          <div>주의 노트 (note warn)</div>
        </div>
      </Card>

      <Card title="목록 테이블" sub="No.·상태처럼 모든 목록 공통 열은 폭을 고정한다">
        <DataTable columns={tableColumns} rows={DEMO_ROWS} rowKey={(r) => r.id} />
      </Card>

      <Card title="반복 카드 리스트" sub="§C — 영양소·약재 등 '마스터 + 카드 N건' 화면이 쓴다">
        <RepeatableCards cards={cards} onChange={setCards} fieldLabel="개선분야(관점)" fieldPlaceholder="예: 대사회복" />
      </Card>

      <Card title="상세 사이드 패널 블록">
        <div style={{ maxWidth: 300 }}>
          <PublishBox status={publishStatus} onStatusChange={setPublishStatus} onSave={() => {}} onDelete={() => {}} />
          <div style={{ marginTop: 14 }}>
            <MetaPanel id="NUT-01" createdAt="2026-07-28T00:00:00" updatedAt="2026-07-28T00:00:00" updatedBy="원장" />
          </div>
        </div>
      </Card>

      <Card title="컴포넌트 → React 매핑" sub="화면을 새로 만들 때 이 표에서 먼저 찾을 것">
        <div style={{ overflowX: 'auto' }}>
          <table className="ds-map">
            <thead>
              <tr>
                <th>컴포넌트</th>
                <th>React</th>
              </tr>
            </thead>
            <tbody>
              {REACT_MAP.map(([label, code]) => (
                <tr key={label}>
                  <td><b>{label}</b></td>
                  <td><code>{code}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}
