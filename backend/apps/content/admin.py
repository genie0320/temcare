from django.contrib import admin

from . import models

# 긴급 데이터 수정 창구(슈퍼유저 전용). docs/08_tech_stack.md §1 "Django Admin 방침".
# 콘텐츠 마스터(개인정보 아닌 것)만 등록한다 — user/diagnosis_result/consent 등은 노출 안 함.
admin.site.register(models.Weakness)
admin.site.register(models.TemType)
admin.site.register(models.Nutrient)
admin.site.register(models.NutrientCard)
admin.site.register(models.Herb)
admin.site.register(models.HerbCard)
admin.site.register(models.Food)
admin.site.register(models.Point)
admin.site.register(models.Article)
admin.site.register(models.HealthSign)
admin.site.register(models.Illness)
admin.site.register(models.Product)
