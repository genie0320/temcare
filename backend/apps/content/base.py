"""콘텐츠 마스터 CRUD 공통 기반.

M1에서 10개 마스터 화면을 만들며 ViewSet마다 같은 코드(_next_XXX_id / _actor_label /
perform_create / perform_update / _sync_weaknesses)가 반복됐다. 여기로 모은다.

이 파일이 동시에 세 가지를 책임진다 — 셋이 같은 지점에서 갈라지기 때문이다:
  1) 중복 제거 (같은 뼈대를 한 곳에)
  2) 약점 태그 필수 검증 (docs/02_architecture_constraints.md §7, docs/05 §G)
  3) 관계 변경의 감사로그 기록 (§1 — through 모델은 AuditedModel이 아니라 구멍이 생긴다)
"""

import re

from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import AdminResourcePermission
from apps.audit import service as audit


def next_id(model, prefix: str, width: int = 2) -> str:
    """`WEAK-01` / `TEM01` 처럼 접두사+일련번호 형태의 다음 id를 만든다.

    구분자 유무는 prefix에 포함해서 넘긴다("WEAK-" vs "TEM").
    """
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    max_n = 0
    for existing in model.objects.values_list("id", flat=True):
        m = pattern.match(existing)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"{prefix}{max_n + 1:0{width}d}"


def sync_relation(instance, *, through, parent_field: str, related_field: str, target_ids) -> None:
    """연결 테이블을 target_ids로 통째로 교체하고, 변경분을 감사로그에 남긴다.

    ★ QuerySet.delete()/bulk_* 금지(docs/08_tech_stack.md §4) — 인스턴스 단위로만 지운다.
    ★ through 모델은 AuditedModel이 아니라 시그널이 뜨지 않는다. 부모 save()는 시그널을
      남기지만 부모 필드가 안 바뀌었으면 before==after라서 '무엇이 바뀌었는지'가 사라진다.
      그래서 여기서 diff를 명시적으로 기록한다(§1).
    """
    related_id_field = f"{related_field}_id"
    current = {
        str(v)
        for v in through.objects.filter(**{parent_field: instance}).values_list(related_id_field, flat=True)
    }
    target = {str(v) for v in (target_ids or [])}

    removed, added = current - target, target - current
    for value in removed:
        through.objects.get(**{parent_field: instance, related_id_field: value}).delete()
    for value in added:
        through.objects.create(**{parent_field: instance, related_id_field: value})

    if removed or added:
        audit.record_relation_change(instance, f"{related_field}_ids", current, target)


class MasterViewSet(ModelViewSet):
    """콘텐츠 마스터 공통 ViewSet. 하위 클래스는 선언만 하면 된다.

        class FoodViewSet(MasterViewSet):
            resource = "adm_025"
            queryset = Food.objects.all()
            id_prefix = "FOOD-"
            list_serializer_class = FoodListSerializer
            detail_serializer_class = FoodDetailSerializer
            search_fields = ["foods", "id", "component", "description"]
            filter_fields = {"polarity": "polarity", "weakness": "weaknesses__id"}
            weakness_through = FoodWeakness
            weakness_parent_field = "food"
    """

    permission_classes = [AdminResourcePermission]

    # 하위 클래스가 채우는 선언들
    id_prefix: str | None = None
    id_width: int = 2
    list_serializer_class = None
    detail_serializer_class = None
    search_fields: list[str] = []
    filter_fields: dict[str, str] = {}

    # 약점 태그 연결 테이블(단일 레코드 + 약점 체크박스 구조인 마스터만 선언).
    # 영양소·약재처럼 카드가 약점을 무는 구조는 _sync_cards 쪽에서 따로 다룬다.
    weakness_through = None
    weakness_parent_field: str | None = None

    # 약점 태그 필수 여부. 고객 화면이 약점 태그로만 콘텐츠를 끌어오므로, 태그 없는
    # 콘텐츠는 저장돼도 영영 노출되지 않는다(docs/02 §7). 기본값 True — 예외인 마스터
    # (약점 자신, 제품)만 False로 끈다.
    weakness_required = True

    def get_serializer_class(self):
        if self.action == "list" and self.list_serializer_class is not None:
            return self.list_serializer_class
        return self.detail_serializer_class

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search and self.search_fields:
            from django.db.models import Q

            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(condition)

        for param, lookup in {**self.filter_fields, "status": "status"}.items():
            value = self.request.query_params.get(param)
            if value:
                qs = qs.filter(**{lookup: value})
        return qs.distinct()

    def _actor_label(self) -> str:
        user = self.request.user
        return user.get_full_name() or user.username

    # ── 약점 태그 ────────────────────────────────────────────────
    def _weakness_ids_in_request(self):
        """요청에 weakness_ids가 있으면 리스트로, 없으면 None(=건드리지 않음)."""
        if "weakness_ids" not in self.request.data:
            return None
        return [str(w) for w in (self.request.data.get("weakness_ids") or [])]

    def _validate_weakness_tags(self, *, creating: bool) -> None:
        """약점 태그 최소 1개를 강제한다.

        ★ '개수' 검증은 하지 않는다 — IDEA끼리 조합되는 예외(TEM54)가 있어서
          정확히 N개 같은 규칙을 걸면 안 된다(docs/05_screen_conventions.md §G).
          여기서 막는 것은 오직 '0개'다.
        """
        if not self.weakness_required or self.weakness_through is None:
            return
        ids = self._weakness_ids_in_request()
        if ids is None:
            # PATCH에서 약점을 아예 언급하지 않았으면 기존 값을 유지한다. 단 생성 시엔
            # 누락 자체가 오류다.
            if creating:
                raise serializers.ValidationError(
                    {"weakness_ids": ["연결 약점은 필수다. 약점 태그가 없으면 고객 화면에 노출되지 않는다."]}
                )
            return
        if not ids:
            raise serializers.ValidationError(
                {"weakness_ids": ["연결 약점은 최소 1개가 필요하다. 태그가 없으면 고객 화면에 노출되지 않는다."]}
            )

    def _sync_weaknesses(self, instance) -> None:
        if self.weakness_through is None or self.weakness_parent_field is None:
            return
        ids = self._weakness_ids_in_request()
        if ids is None:
            return
        sync_relation(
            instance,
            through=self.weakness_through,
            parent_field=self.weakness_parent_field,
            related_field="weakness",
            target_ids=ids,
        )

    # ── 저장 ────────────────────────────────────────────────────
    def perform_create(self, serializer):
        self._validate_weakness_tags(creating=True)
        extra = self.get_create_kwargs(serializer)
        instance = serializer.save(id=next_id(self.queryset.model, self.id_prefix, self.id_width), **extra)
        self._sync_weaknesses(instance)
        self.sync_children(instance)

    def perform_update(self, serializer):
        self._validate_weakness_tags(creating=False)
        extra = self.get_update_kwargs(serializer)
        instance = serializer.save(**extra)
        self._sync_weaknesses(instance)
        self.sync_children(instance)

    def get_create_kwargs(self, serializer) -> dict:
        """serializer.save()에 추가로 넘길 값. 하위 클래스가 확장한다."""
        return {"updated_by": self._actor_label()}

    def get_update_kwargs(self, serializer) -> dict:
        return {"updated_by": self._actor_label()}

    def sync_children(self, instance) -> None:
        """약점 외의 자식(카드·큐레이션 등)을 다루는 훅. 필요한 하위 클래스만 구현한다."""
        return
