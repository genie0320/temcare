"""원장 콘텐츠 입력. `python manage.py import_doctor_content TEM18`

작업 계약: docs/10_content_import.md · 근거: docs/06_decisions.md #38·#39

    ① 문장으로 끊는다   원장 원문 한 열 → 영양소별 문장으로 분해   ┐ 사람이 하고
    ② 중복을 접는다     같은 뜻의 문장은 하나로                    ┘ doctor_data/*.json에 남긴다
    ③ 마스터에 넣는다   (영양소 × 관점) = nutrient_card 한 장       ┐ 이 커맨드가
    ④ 체질에서 조립한다 tem_type_curation(kind='nutrient', sort)    ┘ 하는 일

★ 감사로그 우회 4종(QuerySet 일괄 수정·삭제, bulk_create/bulk_update, 원시 SQL)을
  쓰지 않는다(CLAUDE.md §5). 대량 입력이라 유혹이 크지만 전부 인스턴스 save()/create()/
  delete()다 — 그래야 원장 콘텐츠가 언제 무엇으로 바뀌었는지 audit_log에 남는다.

★ 멱등이다. 같은 파일을 다시 돌리면 (영양소, 관점)이 같은 카드를 찾아 갱신하고,
  체질 큐레이션은 이 파일이 정한 순서로 다시 맞춘다.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.audit import context as audit_context
from apps.content.base import next_id
from apps.content.id_repair import repair_tem_type_ids
from apps.content.models import (
    Nutrient,
    NutrientCard,
    NutrientCardWeakness,
    TemType,
    TemTypeCuration,
    TemTypeWeakness,
    Weakness,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "doctor_data"
ACTOR = "import_doctor_content"


def _require_weakness_tags(cards: list[dict]) -> None:
    """약점 태그 없는 카드를 막는다.

    ★ 서버(_CardMasterViewSet._validate_weakness_tags)가 400으로 막는 규칙과 같은
      것을 여기서도 건다. 커맨드는 뷰를 지나가지 않으므로, 이 검사가 없으면 화면으로는
      만들 수 없는 '태그 없는 카드'가 스크립트로만 생긴다 — 그런 카드는 고객 화면에
      영원히 안 나온다(docs/02_architecture_constraints.md §7).
    """
    for i, card in enumerate(cards, 1):
        if not (card.get("weakness_ids") or []):
            raise CommandError(
                f"{i}번째 영양 카드({card.get('nutrient')})에 연결 약점이 없다. "
                "약점 태그가 없으면 고객 화면에 노출되지 않는다."
            )
        unknown = [w for w in card["weakness_ids"] if not Weakness.objects.filter(pk=w).exists()]
        if unknown:
            raise CommandError(f"{card.get('nutrient')} 카드의 약점 {unknown}이 약점 마스터에 없다.")


def _upsert_nutrient(name: str) -> tuple[Nutrient, bool]:
    """영양소 마스터를 이름으로 찾고, 없으면 만든다.

    시트 표기의 제형 접미사('마그네슘제제')는 doctor_data JSON에서 이미 항목 이름으로
    정리돼 들어온다 — 여기서 이름을 가공하지 않는다.
    """
    nutrient = Nutrient.objects.filter(name=name).first()
    if nutrient is not None:
        return nutrient, False
    nutrient = Nutrient.objects.create(
        id=next_id(Nutrient, "NUT-"),
        name=name,
        status="게시",
        sort=Nutrient.objects.count() + 1,
        updated_by=ACTOR,
    )
    return nutrient, True


def _upsert_card(nutrient: Nutrient, spec: dict) -> tuple[NutrientCard, bool]:
    """(영양소 × 관점) 카드 한 장. 관점이 카드의 정체성이다(#39)."""
    card = nutrient.cards.filter(perspective=spec["perspective"]).first()
    created = card is None
    if created:
        card = NutrientCard(nutrient=nutrient, perspective=spec["perspective"])
    card.description = spec["description"]
    card.sort = spec["_sort"]
    card.save()

    # 약점 태그를 이 카드가 가져야 할 것으로 맞춘다. 인스턴스 단위 create()/delete()만.
    target = set(spec["weakness_ids"])
    current = {row.weakness_id: row for row in NutrientCardWeakness.objects.filter(card=card)}
    for weakness_id in target - set(current):
        NutrientCardWeakness.objects.create(card=card, weakness_id=weakness_id)
    for weakness_id in set(current) - target:
        current[weakness_id].delete()
    return card, created


def _upsert_tem_type(spec: dict) -> TemType:
    tem_type = TemType.objects.filter(pk=spec["id"]).first()
    if tem_type is None:
        raise CommandError(
            f"체질 {spec['id']}이 없다. 이 커맨드는 영양요법 열만 넣는다 — 체질 행 자체를 "
            "만드는 것은 별도 작업이다(docs/10_content_import.md §6)."
        )
    tem_type.name = spec["name"]
    tem_type.nickname = spec["nickname"]
    tem_type.updated_by = ACTOR
    tem_type.save()

    # 약점 태그가 시트와 어긋나면 처방 전체가 어긋난다 — 여기서 맞춘다.
    target = set(spec["weakness_ids"])
    current = {row.weakness_id: row for row in TemTypeWeakness.objects.filter(tem_type=tem_type)}
    for weakness_id in target - set(current):
        TemTypeWeakness.objects.create(tem_type=tem_type, weakness_id=weakness_id)
    for weakness_id in set(current) - target:
        current[weakness_id].delete()
    return tem_type


def _sync_curation(tem_type: TemType, card_ids: list[int]) -> None:
    """④ 조립 — 이 체질이 보여줄 영양 카드와 그 순서.

    원장이 쓴 순서가 곧 노출 순서다. 큐레이션 행이 있으면 고객 API가 약점 자동 조회
    대신 이 목록을 쓴다(customer_views._curated_ref_ids).
    """
    for row in list(TemTypeCuration.objects.filter(tem_type=tem_type, kind="nutrient")):
        row.delete()
    for i, card_id in enumerate(card_ids):
        TemTypeCuration.objects.create(
            tem_type=tem_type, kind="nutrient", ref_id=str(card_id), polarity="", sort=i
        )


class Command(BaseCommand):
    help = "doctor_data/<체질id>.json의 원장 콘텐츠를 콘텐츠 마스터에 넣는다. 멱등."

    def add_arguments(self, parser):
        parser.add_argument("tem_type_id", help="예: TEM18")

    @transaction.atomic
    def handle(self, *args, **options):
        # 감사로그의 actor를 '누가 넣었는지' 알아볼 수 있게 남긴다. 미들웨어가 없는
        # 커맨드 실행이라 여기서 직접 심는다(apps/audit/context.py).
        audit_context.set_context(actor_id=ACTOR, actor_type="system", ip=None)

        type_id = options["tem_type_id"]
        path = DATA_DIR / f"{type_id}.json"
        if not path.exists():
            raise CommandError(f"{path} 가 없다.")
        data = json.loads(path.read_text(encoding="utf-8"))

        # ★ 시드 id 어긋남을 먼저 처리한다(docs/10_content_import.md §5). 이걸 건너뛰고
        #   id 기준으로 넣으면 두 유형이 뒤섞인다.
        repair_tem_type_ids(log=lambda m: self.stdout.write(self.style.WARNING(m)))

        cards_spec = data.get("nutrition") or []
        _require_weakness_tags(cards_spec)

        tem_type = _upsert_tem_type(data["tem_type"])
        self.stdout.write(self.style.SUCCESS(f"체질 {tem_type.pk} · {tem_type.name} · {tem_type.nickname}"))

        card_ids: list[int] = []
        for i, spec in enumerate(cards_spec):
            nutrient, nutrient_created = _upsert_nutrient(spec["nutrient"])
            card, card_created = _upsert_card(nutrient, {**spec, "_sort": i})
            card_ids.append(card.pk)
            marks = ("영양소 신규" if nutrient_created else "영양소 기존") + (
                " · 카드 신규" if card_created else " · 카드 갱신"
            )
            self.stdout.write(
                f"  [{i + 1}] {nutrient.name} ({nutrient.pk}) / 관점 '{card.perspective}' "
                f"/ 약점 {spec['weakness_ids']}  — {marks}"
            )

        _sync_curation(tem_type, card_ids)
        self.stdout.write(
            self.style.SUCCESS(f"체질관리 조립: 영양 카드 {len(card_ids)}장 — {card_ids}")
        )

        for label, lines in (data.get("notes") or {}).items():
            for line in lines:
                self.stdout.write(self.style.WARNING(f"  [{label}] {line}"))
