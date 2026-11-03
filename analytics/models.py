from django.db import models
import uuid

class ProductEvent(models.Model):
    kind=models.CharField(max_length=50)
    execution=models.UUIDField()
    occurred_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['kind','execution'],name='event_kind_execution')]


class TrafficSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.CharField(max_length=16)
    excluded_reason = models.CharField(max_length=16, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    qualified_at = models.DateTimeField(null=True, blank=True)


class TrafficEvent(models.Model):
    kind = models.CharField(max_length=24)
    session = models.ForeignKey(TrafficSession, on_delete=models.CASCADE, related_name='events')
    page = models.CharField(max_length=64, blank=True)
    cta = models.CharField(max_length=40, blank=True)
    operation = models.UUIDField(null=True, blank=True, unique=True)
    effective_navigation = models.BooleanField(default=False)
    occurred_at = models.DateTimeField(auto_now_add=True)
