from django.db import models

from apps.audit.base import AuditedModel


class AppSetting(AuditedModel):
    """schema.app_config. key/value 앱 설정. 예: diagnosis.provider = mock | junchart."""

    key = models.CharField(max_length=100, primary_key=True)
    value = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "app_config"
