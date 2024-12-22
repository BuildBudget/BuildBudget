from typing import Self

from django.db import models


class PullRequest(models.Model):
    id = models.BigIntegerField(primary_key=True)
    number = models.IntegerField(null=True)
    url = models.URLField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.number} - {self.id}"

    @classmethod
    def get_or_create_from_dict_list(cls, prs: list[dict]) -> list[Self]:
        pull_requests = []
        for pr in prs:
            pull_requests.append(cls.get_or_create_from_dict(pr))
        return pull_requests

    @classmethod
    def get_or_create_from_dict(cls, pr: dict) -> Self:
        return PullRequest.objects.update_or_create(
            id=pr["id"],
            defaults={
                "number": pr["number"],
                "url": pr["url"],
            },
        )[0]
