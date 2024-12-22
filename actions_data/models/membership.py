from django.contrib.auth.models import User
from django.db import models


class Membership(models.Model):
    class States(models.TextChoices):
        ACTIVE = "active"
        PENDING = "pending"

    class Roles(models.TextChoices):
        ADMIN = "admin"
        MEMBER = "member"

    organization = models.ForeignKey("OwnerEntity", on_delete=models.CASCADE)
    auth_user = models.ForeignKey(User, on_delete=models.CASCADE)
    state = models.CharField(max_length=50, choices=States)
    role = models.CharField(max_length=50, choices=Roles)
