import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import AdminPermission, AdminProfile, AdminRole, User
from apps.consent.models import ConsentItem, TermsDocument, TermsVersion
from apps.content import models as content
from apps.support.models import AppSetting

ROLES = [
    ("super", "슈퍼관리자", 0),
    ("director", "원장", 1),
    ("editor", "콘텐츠 에디터", 2),
    ("cs", "고객상담", 3),
    ("viewer", "뷰어", 4),
]

# 관리자 화면(M1)이 붙을 때마다 resource id를 여기 추가한다.
SUPER_RESOURCES = ["demo", "adm_003", "adm_002", "adm_022", "adm_023", "adm_025", "adm_026", "adm_007a", "adm_007b", "adm_027", "adm_024"]
SUPER_ACTIONS = ["read", "write", "delete", "publish", "pii_read"]
EDITOR_RESOURCES = ["adm_003", "adm_002", "adm_022", "adm_023", "adm_025", "adm_026", "adm_007a", "adm_007b", "adm_027", "adm_024"]
EDITOR_ACTIONS = ["read", "write", "delete", "publish"]  # 콘텐츠 에디터는 pii_read 없음

# prototype/ollacare.sqlite → 콘텐츠 마스터 모델. docs/07_milestones.md M0 "남은 것".
_SIMPLE_TABLES = [
    ("weakness", content.Weakness),
    ("nutrient", content.Nutrient),
    ("herb", content.Herb),
    ("food", content.Food),
    ("point", content.Point),
    ("health_sign", content.HealthSign),
    ("illness", content.Illness),
    ("product", content.Product),
    ("tem_type", content.TemType),
    ("article", content.Article),
]

_CARD_TABLES = [
    ("nutrient_card", content.NutrientCard, "nutrient_id", "nutrient"),
    ("herb_card", content.HerbCard, "herb_id", "herb"),
]

_WEAKNESS_JOIN_TABLES = [
    ("tem_type_weakness", content.TemTypeWeakness, "type_id", "tem_type", content.TemType),
    ("nutrient_card_weakness", content.NutrientCardWeakness, "card_id", "card", content.NutrientCard),
    ("herb_card_weakness", content.HerbCardWeakness, "card_id", "card", content.HerbCard),
    ("food_weakness", content.FoodWeakness, "food_id", "food", content.Food),
    ("point_weakness", content.PointWeakness, "point_id", "point", content.Point),
    ("article_weakness", content.ArticleWeakness, "article_id", "article", content.Article),
    ("health_sign_weakness", content.HealthSignWeakness, "sign_id", "sign", content.HealthSign),
    ("illness_weakness", content.IllnessWeakness, "illness_id", "illness", content.Illness),
]

_ARTICLE_LINK_TABLES = [
    ("article_food", content.ArticleFood, "food_id", "food", content.Food),
    ("article_point", content.ArticlePoint, "point_id", "point", content.Point),
    ("article_product", content.ArticleProduct, "product_id", "product", content.Product),
]


# ── 약관 · 동의 (sc_092) ─────────────────────────────────────────────
# 항목 구성은 명세서 v5 sc_092의 UI요소 행 그대로다.
# PPT slide 11에는 '개인정보 제3자 제공 동의'도 있으나 "[확인필요] 실제 제3자 제공
# 발생 여부 확정 후 유지/삭제"로 미확정이고 명세서 v5에는 없어 넣지 않았다(명세서 우선).
TERMS_DOCUMENTS = [
    ("tos", "서비스 이용약관", 0),
    ("privacy", "개인정보처리방침", 1),
    ("marketing", "마케팅 정보 수신", 2),
]

# ★ 실제 약관 문안이 아니다. 법률 문서를 임의로 지어내지 않는다 —
#   문진 더미 문항과 같은 원칙(docs/06_decisions.md #24)이다. 시행일자도 미확정(📌).
_PLACEHOLDER_BODY = "[미작성] 실제 약관 문안이 들어갈 자리입니다. 법무 검토된 원문으로 교체해주세요."

CONSENT_ITEMS = [
    # (id, 이름, 필수, 민감정보, 채널, 문서, 순서)
    ("tos", "이용약관 동의", True, False, "", "tos", 0),
    ("privacy", "개인정보 수집·이용 동의", True, False, "", "privacy", 1),
    ("sensitive", "민감정보(건강정보) 수집·이용 동의", True, True, "", "privacy", 2),
    ("age14", "만 14세 이상입니다", True, False, "", None, 3),
    ("mkt", "마케팅 정보 수신 동의", False, False, "push", "marketing", 4),
]


def _seed_consent(stdout, style):
    for doc_id, name, sort in TERMS_DOCUMENTS:
        TermsDocument.objects.update_or_create(id=doc_id, defaults={"name": name, "sort": sort})
        TermsVersion.objects.update_or_create(
            document_id=doc_id,
            version="v0.1",
            defaults={
                "body": _PLACEHOLDER_BODY,
                "effective_at": "2026-01-01",
                "status": "게시",
                "updated_by": "seed_demo",
            },
        )

    for item_id, name, required, sensitive, channel, doc_id, sort in CONSENT_ITEMS:
        ConsentItem.objects.update_or_create(
            id=item_id,
            defaults={
                "name": name,
                "required": required,
                "is_sensitive": sensitive,
                "channel": channel,
                "document_id": doc_id,
                "sort": sort,
                "status": "게시",
            },
        )
    stdout.write(style.SUCCESS(f"consent_item {len(CONSENT_ITEMS)}건 · terms {len(TERMS_DOCUMENTS)}건 (약관 문안은 placeholder)"))


def _seed_content(stdout, style):
    db_path = Path(settings.BASE_DIR).parent / "prototype" / "ollacare.sqlite"
    if not db_path.exists():
        stdout.write(style.WARNING(f"콘텐츠 시드 건너뜀: {db_path} 없음"))
        return

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    def _row_dict(row):
        # sqlite의 NULL은 blank=True 텍스트 컬럼에 그대로 넣으면 NOT NULL 제약에 걸린다.
        return {k: ("" if v is None else v) for k, v in dict(row).items()}

    for table, model in _SIMPLE_TABLES:
        cur.execute(f"SELECT * FROM {table}")  # nosec B608 — table은 위 _SIMPLE_TABLES 상수에서만 온다. 외부 입력 아님.
        n = 0
        for row in cur.fetchall():
            data = _row_dict(row)
            pk = data.pop("id")
            model.objects.update_or_create(id=pk, defaults=data)
            n += 1
        stdout.write(style.SUCCESS(f"{table} {n}건"))

    for table, model, fk_col, fk_field in _CARD_TABLES:
        cur.execute(f"SELECT * FROM {table}")  # nosec B608 — table은 위 _CARD_TABLES 상수에서만 온다. 외부 입력 아님.
        n = 0
        for row in cur.fetchall():
            data = _row_dict(row)
            pk = data.pop("id")
            fk_value = data.pop(fk_col)
            data[fk_field + "_id"] = fk_value
            model.objects.update_or_create(id=pk, defaults=data)
            n += 1
        stdout.write(style.SUCCESS(f"{table} {n}건"))

    for table, through, fk_col, fk_field, _fk_model in _WEAKNESS_JOIN_TABLES:
        cur.execute(f"SELECT * FROM {table}")  # nosec B608 — table은 위 _WEAKNESS_JOIN_TABLES 상수에서만 온다. 외부 입력 아님.
        n = 0
        for row in cur.fetchall():
            through.objects.get_or_create(**{fk_field + "_id": row[fk_col], "weakness_id": row["weakness_id"]})
            n += 1
        stdout.write(style.SUCCESS(f"{table} {n}건"))

    for table, through, fk_col, fk_field, _fk_model in _ARTICLE_LINK_TABLES:
        cur.execute(f"SELECT * FROM {table}")  # nosec B608 — table은 위 _ARTICLE_LINK_TABLES 상수에서만 온다. 외부 입력 아님.
        n = 0
        for row in cur.fetchall():
            through.objects.get_or_create(article_id=row["article_id"], **{fk_field + "_id": row[fk_col]})
            n += 1
        stdout.write(style.SUCCESS(f"{table} {n}건"))

    cur.execute("SELECT * FROM tem_type_illness")
    n = 0
    for row in cur.fetchall():
        content.TemTypeIllness.objects.get_or_create(
            tem_type_id=row["type_id"], illness_id=row["illness_id"], pct=row["pct"], sort=row["sort"]
        )
        n += 1
    stdout.write(style.SUCCESS(f"tem_type_illness {n}건"))

    cur.execute("SELECT * FROM tem_type_curation")
    n = 0
    for row in cur.fetchall():
        content.TemTypeCuration.objects.get_or_create(
            tem_type_id=row["type_id"],
            kind=row["kind"],
            ref_id=row["ref_id"],
            defaults={"polarity": row["polarity"] or "", "sort": row["sort"]},
        )
        n += 1
    stdout.write(style.SUCCESS(f"tem_type_curation {n}건"))

    con.close()


class Command(BaseCommand):
    help = (
        "시드: admin_role/admin_permission, 데모 관리자 계정, app_config, "
        "prototype/ollacare.sqlite의 콘텐츠 마스터. 언제든 다시 돌려도 안전(멱등)."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        for role_id, name, sort in ROLES:
            AdminRole.objects.update_or_create(id=role_id, defaults={"name": name, "sort": sort})
        self.stdout.write(self.style.SUCCESS(f"admin_role {len(ROLES)}건"))

        super_role = AdminRole.objects.get(id="super")
        for resource in SUPER_RESOURCES:
            for action in SUPER_ACTIONS:
                AdminPermission.objects.update_or_create(
                    role=super_role, resource=resource, action=action, defaults={"allowed": True}
                )

        editor_role = AdminRole.objects.get(id="editor")
        for resource in EDITOR_RESOURCES:
            for action in EDITOR_ACTIONS:
                AdminPermission.objects.update_or_create(
                    role=editor_role, resource=resource, action=action, defaults={"allowed": True}
                )
        self.stdout.write(self.style.SUCCESS("admin_permission 시드 완료"))

        admin_user, created = User.objects.get_or_create(
            username="admin@ollacare.local",
            defaults={"email": "admin@ollacare.local", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin_user.set_password("admin1234!")
            admin_user.save()
        AdminProfile.objects.update_or_create(user=admin_user, defaults={"role": super_role})
        self.stdout.write(self.style.SUCCESS(f"데모 관리자 계정: {admin_user.username} / admin1234!"))

        AppSetting.objects.update_or_create(
            key="diagnosis.provider", defaults={"value": "mock", "description": "판별 어댑터 선택"}
        )
        self.stdout.write(self.style.SUCCESS("app_config: diagnosis.provider = mock"))

        _seed_consent(self.stdout, self.style)
        _seed_content(self.stdout, self.style)
