"""콘텐츠 마스터. schema/01_content_master.sql을 Django 모델로 옮긴 것.

M1 순서(docs/07_milestones.md): 약점 → 64유형 → 영양소 → 약재 → 식품군 → 혈자리
→ 건강신호 → 예측질환 → 제품 → 요법관리. 모델은 한 번에 옮기고, CRUD 화면은 이 순서로
하나씩 붙인다.

모든 마스터 테이블은 status/sort/created_at/updated_at/updated_by를 공통으로 가진다
(docs/05_screen_conventions.md §B-5, §F). 약점(n:m) 연결 테이블은 별도 컬럼이 없으면
순수 through 모델로 두고 AuditedModel을 상속하지 않는다 — 실제 감사 대상은 그 태그를
바꾸는 부모 카드/마스터 저장 동작이다.
"""

from django.db import models

from apps.audit.base import AuditedModel

STATUS_CHOICES = [
    ("게시", "게시"),
    ("초안", "초안"),
    ("숨김", "숨김"),
]


class MasterModel(AuditedModel):
    """콘텐츠 마스터 공통 컬럼. docs/05_screen_conventions.md §B-5."""

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="게시")
    sort = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True)

    class Meta:
        abstract = True
        ordering = ["sort"]


# ── 약점 / IDEA 마스터 ────────────────────────────────────────────
class Weakness(MasterModel):
    """schema.weakness. 모든 콘텐츠 연결의 축(CLAUDE.md §6)."""

    WTYPE_CHOICES = [("약점", "약점"), ("IDEA", "IDEA")]

    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    wtype = models.CharField(max_length=10, choices=WTYPE_CHOICES, default="약점")
    catchphrase = models.CharField(max_length=200, blank=True)  # 처방 그룹 제목용
    speaker = models.CharField(max_length=150, blank=True)
    source = models.CharField(max_length=150, blank=True)
    aphorism = models.TextField(blank=True)

    class Meta(MasterModel.Meta):
        db_table = "weakness"

    def __str__(self):
        return self.name

    @property
    def linked_content_count(self) -> int:
        """목록 화면 '연결 콘텐츠수' 열. 이 약점을 참조하는 전 콘텐츠 합계."""
        return (
            self.tem_types.count()
            + self.nutrient_cards.count()
            + self.herb_cards.count()
            + self.foods.count()
            + self.points.count()
            + self.articles.count()
            + self.health_signs.count()
            + self.illnesses.count()
        )


# ── 체질(64유형) 마스터 ───────────────────────────────────────────
class TemType(MasterModel):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=50)
    nickname = models.CharField(max_length=100, blank=True)
    body_value = models.IntegerField(default=50)  # (구) 단일값 · body_min/max로부터 파생 계산해 보존
    body_min = models.IntegerField(default=2)  # 체형특성 5중단점 인덱스(0~4). 2=보통
    body_max = models.IntegerField(default=2)
    body_desc = models.TextField(blank=True)
    herb_title = models.CharField(max_length=200, blank=True)
    herb_desc = models.TextField(blank=True)
    weaknesses = models.ManyToManyField(
        Weakness, through="TemTypeWeakness", related_name="tem_types", blank=True
    )

    class Meta(MasterModel.Meta):
        db_table = "tem_type"

    def __str__(self):
        return self.name


class TemTypeWeakness(models.Model):
    tem_type = models.ForeignKey(TemType, on_delete=models.CASCADE)
    weakness = models.ForeignKey(Weakness, on_delete=models.CASCADE)

    class Meta:
        db_table = "tem_type_weakness"
        constraints = [
            models.UniqueConstraint(fields=["tem_type", "weakness"], name="uniq_tem_type_weakness"),
        ]


class TemTypeIllness(models.Model):
    """체질별 예측질환 발병율(%). 합계 100% 검증 안 함(질환별 독립 발병율)."""

    tem_type = models.ForeignKey(TemType, on_delete=models.CASCADE, related_name="illness_links")
    illness = models.ForeignKey("Illness", on_delete=models.SET_NULL, null=True, blank=True)
    pct = models.IntegerField(default=0)
    sort = models.IntegerField(default=0)

    class Meta:
        db_table = "tem_type_illness"
        ordering = ["sort"]


class TemTypeCuration(models.Model):
    """체질별 큐레이션(수동 노출 선택). 예외적으로 수동 큐레이션하는 유일한 지점(CLAUDE.md §2-4)."""

    KIND_CHOICES = [("nutrient", "영양소"), ("herb", "약재"), ("food", "식품군")]

    tem_type = models.ForeignKey(TemType, on_delete=models.CASCADE, related_name="curations")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    ref_id = models.CharField(max_length=20)  # nutrient_card / herb_card / food의 id
    polarity = models.CharField(max_length=10, blank=True)  # food 전용: 권장 | 제한
    sort = models.IntegerField(default=0)

    class Meta:
        db_table = "tem_type_curation"
        ordering = ["sort"]


# ── 영양소 마스터 + 약점별 관점 카드 ──────────────────────────────
class Nutrient(MasterModel):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    image = models.CharField(max_length=255, blank=True)  # 파일 스토리지 경로/URL. docs/04_design_system.md §4 — base64 인라인 금지.

    class Meta(MasterModel.Meta):
        db_table = "nutrient"

    def __str__(self):
        return self.name


class NutrientCard(AuditedModel):
    """같은 영양소, 다른 관점. 약점은 카드에 n:m으로 붙는다(약점당 카드 1개가 아님)."""

    nutrient = models.ForeignKey(Nutrient, on_delete=models.CASCADE, related_name="cards")
    perspective = models.CharField(max_length=100, blank=True)  # 개선분야(관점)
    description = models.TextField(blank=True)
    sort = models.IntegerField(default=0)
    weaknesses = models.ManyToManyField(
        Weakness, through="NutrientCardWeakness", related_name="nutrient_cards", blank=True
    )

    class Meta:
        db_table = "nutrient_card"
        ordering = ["sort"]


class NutrientCardWeakness(models.Model):
    card = models.ForeignKey(NutrientCard, on_delete=models.CASCADE)
    weakness = models.ForeignKey(Weakness, on_delete=models.CASCADE)

    class Meta:
        db_table = "nutrient_card_weakness"
        constraints = [
            models.UniqueConstraint(fields=["card", "weakness"], name="uniq_nutrient_card_weakness"),
        ]


# ── 약재(인생처방) 마스터 + 약점별 효능 카드 ──────────────────────
class Herb(MasterModel):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    hanja = models.CharField(max_length=100, blank=True)
    image = models.CharField(max_length=255, blank=True)  # 파일 스토리지 경로/URL. docs/04_design_system.md §4 — base64 인라인 금지.

    class Meta(MasterModel.Meta):
        db_table = "herb"

    def __str__(self):
        return self.name


class HerbCard(AuditedModel):
    herb = models.ForeignKey(Herb, on_delete=models.CASCADE, related_name="cards")
    mechanism = models.CharField(max_length=100, blank=True)  # 효능기전
    description = models.TextField(blank=True)
    sort = models.IntegerField(default=0)
    weaknesses = models.ManyToManyField(
        Weakness, through="HerbCardWeakness", related_name="herb_cards", blank=True
    )

    class Meta:
        db_table = "herb_card"
        ordering = ["sort"]


class HerbCardWeakness(models.Model):
    card = models.ForeignKey(HerbCard, on_delete=models.CASCADE)
    weakness = models.ForeignKey(Weakness, on_delete=models.CASCADE)

    class Meta:
        db_table = "herb_card_weakness"
        constraints = [
            models.UniqueConstraint(fields=["card", "weakness"], name="uniq_herb_card_weakness"),
        ]


# ── 식품군 마스터 ─────────────────────────────────────────────────
class Food(MasterModel):
    POLARITY_CHOICES = [("권장", "권장"), ("제한", "제한")]

    id = models.CharField(max_length=20, primary_key=True)
    polarity = models.CharField(max_length=10, choices=POLARITY_CHOICES, default="권장")
    component = models.CharField(max_length=200, blank=True)  # 핵심성분
    foods = models.TextField(blank=True)  # 식품 목록
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)  # 파일 스토리지 경로/URL. docs/04_design_system.md §4 — base64 인라인 금지.
    weaknesses = models.ManyToManyField(
        Weakness, through="FoodWeakness", related_name="foods", blank=True
    )

    class Meta(MasterModel.Meta):
        db_table = "food"


class FoodWeakness(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    weakness = models.ForeignKey(Weakness, on_delete=models.CASCADE)

    class Meta:
        db_table = "food_weakness"
        constraints = [
            models.UniqueConstraint(fields=["food", "weakness"], name="uniq_food_weakness"),
        ]


# ── 혈자리 마스터 ─────────────────────────────────────────────────
class Point(MasterModel):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    hanja = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    tip = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)  # 파일 스토리지 경로/URL. docs/04_design_system.md §4 — base64 인라인 금지.
    video = models.CharField(max_length=255, blank=True)
    weaknesses = models.ManyToManyField(
        Weakness, through="PointWeakness", related_name="points", blank=True
    )

    class Meta(MasterModel.Meta):
        db_table = "point"

    def __str__(self):
        return self.name


class PointWeakness(models.Model):
    point = models.ForeignKey(Point, on_delete=models.CASCADE)
    weakness = models.ForeignKey(Weakness, on_delete=models.CASCADE)

    class Meta:
        db_table = "point_weakness"
        constraints = [
            models.UniqueConstraint(fields=["point", "weakness"], name="uniq_point_weakness"),
        ]


# ── 체질별 관리법(아티클: 식이/지압/생활/뜸) ──────────────────────
class Article(MasterModel):
    KIND_CHOICES = [("식이", "식이"), ("지압·마사지", "지압·마사지"), ("생활", "생활"), ("뜸", "뜸")]

    id = models.CharField(max_length=20, primary_key=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="식이")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)  # HTML
    image = models.CharField(max_length=255, blank=True)  # 파일 스토리지 경로/URL. docs/04_design_system.md §4 — base64 인라인 금지.
    video = models.CharField(max_length=255, blank=True)
    weaknesses = models.ManyToManyField(
        Weakness, through="ArticleWeakness", related_name="articles", blank=True
    )
    linked_foods = models.ManyToManyField(Food, through="ArticleFood", related_name="articles", blank=True)
    linked_points = models.ManyToManyField(Point, through="ArticlePoint", related_name="articles", blank=True)
    linked_products = models.ManyToManyField(
        "Product", through="ArticleProduct", related_name="articles", blank=True
    )

    class Meta(MasterModel.Meta):
        db_table = "article"

    def __str__(self):
        return self.title


class ArticleWeakness(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    weakness = models.ForeignKey(Weakness, on_delete=models.CASCADE)

    class Meta:
        db_table = "article_weakness"
        constraints = [
            models.UniqueConstraint(fields=["article", "weakness"], name="uniq_article_weakness"),
        ]


class ArticleFood(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)

    class Meta:
        db_table = "article_food"
        constraints = [models.UniqueConstraint(fields=["article", "food"], name="uniq_article_food")]


class ArticlePoint(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    point = models.ForeignKey(Point, on_delete=models.CASCADE)

    class Meta:
        db_table = "article_point"
        constraints = [models.UniqueConstraint(fields=["article", "point"], name="uniq_article_point")]


class ArticleProduct(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)

    class Meta:
        db_table = "article_product"
        constraints = [models.UniqueConstraint(fields=["article", "product"], name="uniq_article_product")]


# ── 건강신호 마스터 ───────────────────────────────────────────────
class HealthSign(MasterModel):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    note = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)  # 파일 스토리지 경로/URL. docs/04_design_system.md §4 — base64 인라인 금지.
    weaknesses = models.ManyToManyField(
        Weakness, through="HealthSignWeakness", related_name="health_signs", blank=True
    )

    class Meta(MasterModel.Meta):
        db_table = "health_sign"

    def __str__(self):
        return self.name


class HealthSignWeakness(models.Model):
    sign = models.ForeignKey(HealthSign, on_delete=models.CASCADE)
    weakness = models.ForeignKey(Weakness, on_delete=models.CASCADE)

    class Meta:
        db_table = "health_sign_weakness"
        constraints = [
            models.UniqueConstraint(fields=["sign", "weakness"], name="uniq_health_sign_weakness"),
        ]


# ── 예측질환 마스터 ───────────────────────────────────────────────
class Illness(MasterModel):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)  # 보존 · 현재 UI 미노출
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)  # 파일 스토리지 경로/URL. docs/04_design_system.md §4 — base64 인라인 금지.
    weaknesses = models.ManyToManyField(
        Weakness, through="IllnessWeakness", related_name="illnesses", blank=True
    )

    class Meta(MasterModel.Meta):
        db_table = "illness"

    def __str__(self):
        return self.name


class IllnessWeakness(models.Model):
    illness = models.ForeignKey(Illness, on_delete=models.CASCADE)
    weakness = models.ForeignKey(Weakness, on_delete=models.CASCADE)

    class Meta:
        db_table = "illness_weakness"
        constraints = [
            models.UniqueConstraint(fields=["illness", "weakness"], name="uniq_illness_weakness"),
        ]


# ── 제품 마스터 ───────────────────────────────────────────────────
class Product(MasterModel):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=255, blank=True)  # 파일 스토리지 경로/URL. docs/04_design_system.md §4 — base64 인라인 금지.
    url = models.CharField(max_length=500, blank=True)

    class Meta(MasterModel.Meta):
        db_table = "product"

    def __str__(self):
        return self.name


# ── 템라이프(뉴스피드형 콘텐츠) ─────────────────────────────────────
class LifeArticle(MasterModel):
    """schema 미신설 상태였던 tem_daily를 2차 착수 시점에 신설(docs/06_decisions.md #11 갱신).

    요법관리(article)와 달리 약점 태그로 자동 노출되지 않는다 — 카테고리 피드로 큐레이션한다.
    """

    CATEGORY_CHOICES = [
        ("체온", "체온"),
        ("먹고싸고", "먹고싸고"),
        ("멘탈", "멘탈"),
        ("체질이야기", "체질이야기"),
    ]

    id = models.CharField(max_length=20, primary_key=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="체온")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)  # HTML, 리치에디터
    image = models.CharField(max_length=255, blank=True)  # 키비주얼. docs/04_design_system.md §4 — base64 인라인 금지.
    video = models.CharField(max_length=255, blank=True)

    class Meta(MasterModel.Meta):
        db_table = "tem_daily"

    def __str__(self):
        return self.title


class LifeArticleLink(models.Model):
    """템라이프 글 하단의 '다른 템콘텐츠' 연결 — 콘텐츠 마스터 8종 전체에서 선택 가능하다.

    TemTypeCuration과 같은 kind+ref_id 방식을 쓰지만 목적은 다르다. TemTypeCuration은
    처방 노출을 수동으로 제어하는 유일한 예외 지점(CLAUDE.md §2-4)이고, 이건 글 하단의
    '더 읽어보기' 편집 링크일 뿐 처방 스트림 노출 로직과는 무관하다.
    """

    KIND_CHOICES = [
        ("nutrient", "영양소"),
        ("herb", "약재"),
        ("food", "식품군"),
        ("point", "혈자리"),
        ("health_sign", "건강신호"),
        ("illness", "예측질환"),
        ("product", "제품"),
        ("article", "요법관리"),
    ]

    life_article = models.ForeignKey(LifeArticle, on_delete=models.CASCADE, related_name="content_links")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    ref_id = models.CharField(max_length=20)
    sort = models.IntegerField(default=0)

    class Meta:
        db_table = "tem_life_content_link"
        ordering = ["sort"]
        constraints = [
            models.UniqueConstraint(fields=["life_article", "kind", "ref_id"], name="uniq_life_article_link"),
        ]


class LifeArticleRelated(models.Model):
    """관련 기사 — 템라이프끼리의 자기참조(단방향). schema 상 tem_related에 해당."""

    from_article = models.ForeignKey(LifeArticle, on_delete=models.CASCADE, related_name="related_links")
    to_article = models.ForeignKey(LifeArticle, on_delete=models.CASCADE, related_name="+")
    sort = models.IntegerField(default=0)

    class Meta:
        db_table = "tem_related"
        ordering = ["sort"]
        constraints = [
            models.UniqueConstraint(fields=["from_article", "to_article"], name="uniq_life_article_related"),
        ]
