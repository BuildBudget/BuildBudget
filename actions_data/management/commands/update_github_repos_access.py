from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from actions_data.models import UserProfile  # Replace with your actual app name


class Command(BaseCommand):
    help = "Updates GitHub organizations and repositories for all UserProfile instances"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user", type=str, help="Username to update specific user only"
        )
        parser.add_argument(
            "--skip-errors",
            action="store_true",
            help="Continue processing even if some profiles fail",
        )

    def handle(self, *args, **options):
        # Get the queryset of profiles to process
        if options["user"]:
            profiles = UserProfile.objects.filter(user__username=options["user"])
            if not profiles.exists():
                raise CommandError(f"User '{options['user']}' not found")
        else:
            profiles = UserProfile.objects.all()

        total = profiles.count()
        processed = 0
        errors = 0

        self.stdout.write(f"Found {total} profile(s) to process")

        for profile in profiles:
            try:
                with transaction.atomic():
                    self.stdout.write(f"Processing {profile.user.username}...")
                    if profile.github_token:
                        profile.update_github_orgs_and_repos_with_app_installed()
                        processed += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipping {profile.user.username} - No GitHub token found"
                            )
                        )
            except Exception as e:
                errors += 1
                error_msg = f"Error processing {profile.user.username}: {str(e)}"
                if options["skip_errors"]:  # Changed from skip-errors to skip_errors
                    self.stderr.write(self.style.WARNING(error_msg))
                else:
                    raise CommandError(error_msg)

        self.stdout.write(
            self.style.SUCCESS(f"\nCompleted: {processed} processed, {errors} errors")
        )
