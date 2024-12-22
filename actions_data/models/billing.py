from django.db import models


class Billing(models.Model):
    total_minutes_used = models.IntegerField()
    total_paid_minutes_used = models.IntegerField()
    included_minutes = models.IntegerField()
    minutes_used_breakdown = models.JSONField()
