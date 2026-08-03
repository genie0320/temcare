from django.db import models

from apps.audit.base import AuditedModel

# 협력 한의원 (schema/02_service_1st.sql `clinic`, 관리자 adm_040, 고객 sc_040).
#
# ★ 이 테이블이 서비스의 목적지다. 앱은 약식 문진·약식 결과까지만 하고, "정확히
#   알고 싶으면 협력 한의원에서 130문항 정밀 문진"으로 보낸다(docs/06_decisions.md #8).
#   처방 스트림 끝의 CTA가 여기로 온다.
#
# 초기 3곳(안양 1·지방 2) 규모라 **지도 임베드·검색·거리순 정렬을 만들지 않는다**
# (명세서 sc_040 비고). 좌표 컬럼도 두지 않는다 — 지도는 map_url로 외부 앱에 넘긴다.


class Clinic(AuditedModel):
    STATUS_CHOICES = [("게시", "게시"), ("숨김", "숨김")]

    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    director = models.CharField(max_length=50, blank=True)  # 원장명
    sido = models.CharField(max_length=20, blank=True)
    sigungu = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    hours = models.TextField(blank=True)  # 진료시간(자유 텍스트 — 요일별 구조를 만들 규모가 아니다)
    intro = models.TextField(blank=True)  # 한 줄 소개
    image = models.CharField(max_length=255, blank=True)
    map_url = models.CharField(max_length=500, blank=True)  # 카카오/네이버 지도 링크
    homepage = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="게시")
    sort = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "clinic"
        ordering = ["sort", "id"]

    def __str__(self):
        return self.name

    @property
    def region(self) -> str:
        """'경기 안양시'처럼 한 줄로 합친 지역 표기. 화면에서 매번 이어붙이지 않게."""
        return " ".join(part for part in (self.sido, self.sigungu) if part)
