"""고객용 콘텐츠 조회 API — 읽기 전용.

`/api/content/*`(views.py)는 **관리자 전용**이다(AdminResourcePermission). 고객 화면이
같은 엔드포인트를 쓸 수 없어서 여기를 따로 둔다. 경로도 `/api/result/*`로 나눈다.

노출 원칙
- 티저(sc_010)는 **비로그인**으로 열린다. 그래서 유형명·별명만 준다 — 그 이상은
  가입 후에야 볼 수 있어야 깔때기가 성립한다(docs/06_decisions.md #8).
- 상세(sc_004b~sc_006)는 로그인 + 본인의 최신 진단 결과 기준으로만 준다.
- 어느 쪽이든 **status='게시'인 것만** 내보낸다. 초안·숨김이 고객에게 새면 안 된다.
"""

from rest_framework import status as http
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.diagnosis.mapping import raw_to_type_id
from apps.diagnosis.models import DiagnosisResult

from .models import Article, Food, HealthSign, HerbCard, NutrientCard, TemType

PUBLISHED = "게시"


def _teaser(tem_type: TemType) -> dict:
    return {"typeId": tem_type.pk, "name": tem_type.name, "nickname": tem_type.nickname}


def _my_tem_type(user, *prefetch: str) -> tuple[str | None, TemType | None]:
    """로그인 사용자의 **최신** 진단 결과 → 체질. 결과가 없으면 (None, None).

    -id를 같이 넣는다: 같은 초에 두 건이 들어오면 created_at만으로는 순서가 흔들려
    "최신 결과"가 매번 달라진다(실제로 테스트에서 먼저 잡혔다).
    """
    result = DiagnosisResult.objects.filter(user=user).order_by("-created_at", "-id").first()
    if result is None:
        return None, None

    type_id = result.type_id or raw_to_type_id(result.raw_value)
    tem_type = (
        TemType.objects.filter(pk=type_id, status=PUBLISHED).prefetch_related(*prefetch).first()
    )
    return type_id, tem_type


def _published_weaknesses(tem_type: TemType) -> list:
    return [w for w in tem_type.weaknesses.all() if w.status == PUBLISHED]


def _illnesses_of(tem_type: TemType) -> list[dict]:
    """체질별 예측질환. **질환 하나당 한 줄**로 접어서 내보낸다.

    ★ 같은 질환이 두 번 연결돼 있어도 고객에게 두 번 보이면 안 된다. 발병율은
      질환별 독립 수치라 같은 질환이 두 줄인 것 자체가 의미가 없다.
      로컬 DB에는 실제로 이런 중복이 생긴다 — 관리자 화면의 '통째로 교체'와
      seed_demo가 겹치면 sort만 다른 쌍둥이 행이 남는다(docs/06_decisions.md #21).
      데이터를 고치는 것과 별개로, 읽는 쪽이 중복에 무너지지 않아야 한다.
    """
    seen: set[str] = set()
    rows: list[dict] = []
    for link in tem_type.illness_links.all():
        if not link.illness_id or link.illness.status != PUBLISHED:
            continue
        if link.illness_id in seen:
            continue
        seen.add(link.illness_id)
        rows.append(
            {
                "id": link.illness.pk,
                "name": link.illness.name,
                "pct": link.pct,
                "description": link.illness.description,
                "image": link.illness.image,
            }
        )
    return rows


@api_view(["GET"])
@permission_classes([AllowAny])
def result_teaser(request, raw: int):
    """sc_010 결과 티저 — 유형명/별명만. 비로그인으로 호출된다.

    ★ 여기에 약점·건강신호·처방을 얹지 말 것. 티저가 상세를 대신해 버리면
      '자세히 보기 → 가입' 동선이 무너진다.
    """
    type_id = raw_to_type_id(raw)
    if type_id is None:
        return Response({"detail": "결과값 범위를 벗어났어요."}, status=http.HTTP_400_BAD_REQUEST)

    tem_type = TemType.objects.filter(pk=type_id, status=PUBLISHED).first()
    if tem_type is None:
        # 로컬 개발에서 자주 만난다 — tem_type 시드가 아직 6개뿐이라(📌) 대부분의
        # raw가 여기 걸린다. 화면이 깨지지 않도록 found=False로 알려준다.
        return Response({"typeId": type_id, "found": False})

    return Response({**_teaser(tem_type), "found": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_result(request):
    """sc_004b 체질 결과 홈 + sc_005 건강신호 + sc_006 예측질환이 쓰는 상세.

    세 화면이 같은 데이터를 쓰므로 한 번에 내려준다 — 화면마다 왕복하면 탭을 옮길
    때마다 로딩이 보인다.
    """
    type_id, tem_type = _my_tem_type(request.user, "weaknesses", "illness_links__illness")
    if type_id is None:
        return Response({"hasResult": False})
    if tem_type is None:
        return Response({"hasResult": True, "typeId": type_id, "found": False})

    weaknesses = _published_weaknesses(tem_type)
    weakness_ids = [w.pk for w in weaknesses]

    # 건강신호는 체질에 직접 붙지 않고 **약점 태그로 자동 구성**된다(CLAUDE.md §2-4).
    health_signs = (
        HealthSign.objects.filter(weaknesses__id__in=weakness_ids, status=PUBLISHED).distinct()
        if weakness_ids
        else HealthSign.objects.none()
    )

    return Response(
        {
            "hasResult": True,
            "found": True,
            **_teaser(tem_type),
            # 체형특성 게이지(sc_004b UI요소 4번). 0~4 인덱스다 — 0~100 값이 아니다(결정 #19).
            "body": {"min": tem_type.body_min, "max": tem_type.body_max, "desc": tem_type.body_desc},
            "weaknesses": [{"id": w.pk, "name": w.name, "catchphrase": w.catchphrase} for w in weaknesses],
            "healthSigns": [{"id": s.pk, "name": s.name, "note": s.note, "image": s.image} for s in health_signs],
            # 발병율(%)은 질환별 독립 수치다. 합계 100%가 아니다(명세서 sc_006).
            "illnesses": _illnesses_of(tem_type),
        }
    )


# ── sc_007 처방 스트림 "내 몸을 아끼는 길" ────────────────────────
#
# 영양 → 식이 → 생활 → 약재 4정거장(결정 #2). 한 화면 스크롤이므로 API도 한 번에
# 내려준다 — 정거장마다 왕복하면 스크롤 도중에 로딩이 끼어들어 크레센도가 끊긴다.
#
# ★ 결과화면(판정)에는 이것들이 들어가지 않는다. 체질에 **속한 것**(약점·건강신호·
#   질환)은 결과에, 체질을 **다스리는 것**(영양·식이·생활·약재)은 여기에.
#
# ★ 내용은 체질별 수동 큐레이션이 아니라 **약점 태그 자동 조회**다(CLAUDE.md §2-4).
#   유일한 예외가 tem_type_curation이고, 그 체질·종류에 큐레이션 행이 있으면 그것이
#   노출 목록과 순서를 대신한다. 영양·약재·식품군 셋만 해당하고 요법은 아니다.


def _curated_ref_ids(tem_type: TemType, kind: str) -> list[str] | None:
    """체질별 노출 선택. 행이 없으면 None을 돌려 "자동 구성"으로 떨어뜨린다.

    빈 리스트와 None을 구분하는 것이 핵심이다 — None은 "고른 적 없음"이고 빈
    리스트라면 "아무것도 안 보이게 골랐음"이라 뜻이 정반대다.
    """
    rows = [c for c in tem_type.curations.all() if c.kind == kind]  # Meta.ordering = sort
    return [c.ref_id for c in rows] if rows else None


def _in_curated_order(items: list, ref_ids: list[str], key) -> list:
    order = {ref: i for i, ref in enumerate(ref_ids)}
    return sorted(items, key=lambda item: order.get(str(key(item)), len(order)))


def _numeric(ref_ids: list[str]) -> list[str]:
    """카드 pk는 정수인데 ref_id는 문자열 컬럼이다. 숫자가 아닌 값이 섞이면
    쿼리가 ValueError로 죽으므로 미리 걸러낸다."""
    return [r for r in ref_ids if r.isdigit()]


def _nutrition_of(tem_type: TemType, weakness_ids: list[str]) -> list[dict]:
    """정거장 ① 영양. 카드 단위 = (영양소 × 관점)이라 같은 영양소가 두 번 나올 수 있다."""
    curated = _curated_ref_ids(tem_type, "nutrient")
    qs = NutrientCard.objects.select_related("nutrient")
    if curated is not None:
        qs = qs.filter(pk__in=_numeric(curated))
    else:
        qs = qs.filter(weaknesses__id__in=weakness_ids).distinct()

    # 카드에는 status가 없다. 게시 여부는 영양소 마스터가 가진다.
    cards = [c for c in qs if c.nutrient.status == PUBLISHED]
    if curated is not None:
        cards = _in_curated_order(cards, curated, lambda c: c.pk)
    return [
        {
            "id": c.pk,
            "name": c.nutrient.name,
            "image": c.nutrient.image,
            "perspective": c.perspective,
            "description": c.description,
        }
        for c in cards
    ]


def _diet_of(tem_type: TemType, weakness_ids: list[str]) -> dict:
    """정거장 ② 식이 — 식탁 신호등(권장/제한 2블록)."""
    curated = _curated_ref_ids(tem_type, "food")
    qs = Food.objects.filter(status=PUBLISHED)
    if curated is not None:
        qs = qs.filter(pk__in=curated)
    else:
        qs = qs.filter(weaknesses__id__in=weakness_ids).distinct()

    foods = list(qs)
    if curated is not None:
        foods = _in_curated_order(foods, curated, lambda f: f.pk)

    def row(food: Food) -> dict:
        return {
            "id": food.pk,
            "component": food.component,
            "foods": food.foods,
            "description": food.description,
            "image": food.image,
        }

    # 권장/제한은 **식품군 마스터의 polarity가 정본**이다. 큐레이션 행에도 같은 열이
    # 있지만 그건 관리자 화면의 사본이라, 둘이 어긋나면 마스터를 따른다.
    return {
        "good": [row(f) for f in foods if f.polarity == "권장"],
        "limit": [row(f) for f in foods if f.polarity == "제한"],
    }


def _life_of(weakness_ids: list[str]) -> list[dict]:
    """정거장 ③ 생활 — 요법관리(식이/지압·마사지/생활/뜸).

    요법은 큐레이션 대상이 아니다. 오직 약점 태그로만 붙는다(결정 #3).
    """
    if not weakness_ids:
        return []
    articles = (
        Article.objects.filter(weaknesses__id__in=weakness_ids, status=PUBLISHED)
        .distinct()
        .prefetch_related("weaknesses")
    )
    return [
        {
            "id": a.pk,
            "kind": a.kind,
            "title": a.title,
            "body": a.body,
            "image": a.image,
            "video": a.video,
            # "지압·마사지 · 소화불량"처럼 왜 이 요법이 나왔는지 한 줄로 보여주기 위한 것.
            # **이 체질이 가진 약점만** 남긴다 — 요법에 붙은 다른 약점까지 보여주면
            # 내 것이 아닌 이야기가 섞인다.
            "weaknesses": [w.name for w in a.weaknesses.all() if w.pk in set(weakness_ids)],
        }
        for a in articles
    ]


def _herb_groups_of(tem_type: TemType, weaknesses: list) -> list[dict]:
    """정거장 ④ 약재 — 약점 캐치프레이즈로 묶는다("'똥 막힌 하수도'를 위한 · 변비").

    ★ 한 약재 카드가 약점 여러 개에 걸려도 체질의 약점 순서상 **처음 만나는 한 곳**
      에만 넣는다. 같은 약재가 두 그룹에 보이면 "왜 두 번 나오지"가 되는데, 여기가
      크레센도의 마지막 장면이라 특히 눈에 띈다.
    """
    curated = _curated_ref_ids(tem_type, "herb")
    weakness_ids = [w.pk for w in weaknesses]
    qs = HerbCard.objects.select_related("herb").prefetch_related("weaknesses")
    if curated is not None:
        qs = qs.filter(pk__in=_numeric(curated))
    else:
        qs = qs.filter(weaknesses__id__in=weakness_ids).distinct()

    cards = [c for c in qs if c.herb.status == PUBLISHED]
    if curated is not None:
        cards = _in_curated_order(cards, curated, lambda c: c.pk)

    buckets: dict[str, list] = {w.pk: [] for w in weaknesses}
    orphans: list = []
    for card in cards:
        tagged = {w.pk for w in card.weaknesses.all()}
        home = next((wid for wid in weakness_ids if wid in tagged), None)
        if home is None:
            # 큐레이션으로 고른 약재인데 이 체질의 약점과 겹치지 않는 경우다.
            # 조용히 버리면 원장이 고른 것이 사라지므로, 제목 없는 그룹으로 남긴다.
            orphans.append(card)
        else:
            buckets[home].append(card)

    def item(card: HerbCard) -> dict:
        return {
            "id": card.pk,
            "name": card.herb.name,
            "hanja": card.herb.hanja,
            "image": card.herb.image,
            "mechanism": card.mechanism,
            "description": card.description,
        }

    groups = [
        {
            "weaknessId": w.pk,
            "weaknessName": w.name,
            "catchphrase": w.catchphrase,
            "items": [item(c) for c in buckets[w.pk]],
        }
        for w in weaknesses
        if buckets[w.pk]
    ]
    if orphans:
        groups.append(
            {
                "weaknessId": None,
                "weaknessName": "",
                "catchphrase": "",
                "items": [item(c) for c in orphans],
            }
        )
    return groups


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_prescription(request):
    """sc_007 처방 스트림. 4정거장을 한 번에 내려준다."""
    type_id, tem_type = _my_tem_type(request.user, "weaknesses", "curations")
    if type_id is None:
        return Response({"hasResult": False})
    if tem_type is None:
        return Response({"hasResult": True, "typeId": type_id, "found": False})

    weaknesses = _published_weaknesses(tem_type)
    weakness_ids = [w.pk for w in weaknesses]

    return Response(
        {
            "hasResult": True,
            "found": True,
            **_teaser(tem_type),
            "weaknesses": [
                {"id": w.pk, "name": w.name, "catchphrase": w.catchphrase} for w in weaknesses
            ],
            "nutrition": _nutrition_of(tem_type, weakness_ids),
            "diet": _diet_of(tem_type, weakness_ids),
            "life": _life_of(weakness_ids),
            "herb": {
                # 약재 정거장의 제목·리드는 체질마다 원장이 직접 쓴다(자동 구성 아님).
                "title": tem_type.herb_title,
                "desc": tem_type.herb_desc,
                "groups": _herb_groups_of(tem_type, weaknesses),
            },
        }
    )
