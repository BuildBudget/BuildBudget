from typing import Optional

from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.crypto import get_random_string
from social_django.models import UserSocialAuth

from actions_data.github_client import (
    get_github_orgs_and_repos_with_app_installed,
    extract_installations,
    UserOrg,
)
from actions_data.models import Installation, Repository


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="userprofile"
    )
    webhook_secret = models.CharField(max_length=64)
    use_as_global_token = models.BooleanField(default=False)
    repositories = models.ManyToManyField("Repository", related_name="users")

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def github_token(self) -> Optional[str]:
        try:
            return self.user.social_auth.get(provider="github-app").extra_data[
                "access_token"
            ]
        except UserSocialAuth.DoesNotExist:
            return None

    @property
    def webhook_settings_url(self):
        if self.user.social_auth.exists():
            return reverse("settings")
        else:
            return reverse("settings_webhooks_github_es")

    @transaction.atomic
    def refresh_installations(self, installations):
        self.user.installations.clear()
        for installation in installations:
            db_installation = (
                Installation.objects.update_or_create_from_client_instance(installation)
            )
            self.user.installations.add(db_installation)

    @transaction.atomic
    def refresh_repos(self, orgs_and_repos: list[UserOrg]):
        self.repositories.clear()
        for user_org in orgs_and_repos:
            for repo in user_org.user_repos:
                db_repo = Repository.objects.get_or_create_from_client_response(
                    repo.repo
                )
                self.repositories.add(db_repo)

    def update_github_orgs_and_repos_with_app_installed(self):
        orgs_and_repos = get_github_orgs_and_repos_with_app_installed(self.github_token)
        installations = extract_installations(orgs_and_repos)
        self.refresh_installations(installations)
        self.refresh_repos(orgs_and_repos)
        return orgs_and_repos


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, webhook_secret=get_random_string(64))


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
