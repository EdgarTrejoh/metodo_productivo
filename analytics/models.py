from django.db import models
class ProductEvent(models.Model):
    kind=models.CharField(max_length=50)
    execution=models.UUIDField()
    occurred_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['kind','execution'],name='event_kind_execution')]
