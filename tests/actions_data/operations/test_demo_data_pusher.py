import responses
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from unittest.mock import patch, MagicMock, call
from datetime import timedelta

from freezegun import freeze_time

from actions_data.models import OwnerEntity, UserProfile, Installation
from social_django.models import UserSocialAuth

from actions_data.operations.demo_data_pusher import (
    DemoDataPusher,
    get_auth_tokens,
    link_demo_repos_to_demo_user,
)
from actions_data.tasks import (
    process_webhook_event,
    push_demo_data_to_webhook_events,
    process_organization_data,
)


class DemoDataPusherTestCase(TestCase):

    fixtures = [
        "tests/fixtures/authusers.yaml",
        "tests/fixtures/usersocialauths.yaml",
        "tests/fixtures/ownerentities.yaml",
    ]

    def setUp(self):
        user = UserProfile.objects.get(user_id=34)
        user.use_as_global_token = True
        user.save()
        another = UserProfile.objects.get(user_id=3)
        another.use_as_global_token = True
        another.save()
        self.demo_installation = Installation.objects.demo_installation()
        self.demo_user = User.objects.get(username=settings.DEMO_USERNAME)
        self.mock_process_webhook_event = MagicMock()

    def test_get_auth_tokens(self):
        tokens = get_auth_tokens()
        self.assertCountEqual(tokens, ["token1", "token3"])

    @responses.activate
    @freeze_time("2024-11-11T09:53:23.329544Z")
    def test_push_demo_data_to_webhook_events(self):
        responses._add_from_file(
            file_path="tests/responses/test_push_demo_data_to_webhook_events.yaml"
        )
        pusher = DemoDataPusher(webhook_processing_function=process_webhook_event)
        pusher.push_demo_data_to_webhook_events(timedelta(minutes=5))
        self.assertEqual(
            OwnerEntity.objects.get(login="ohmyzsh").repositories.count(), 1
        )
        self.assertEqual(self.demo_installation.webhook_events.count(), 2)
        link_demo_repos_to_demo_user()
        demo_user_repos = self.demo_user.userprofile.repositories.all()
        self.assertEqual(demo_user_repos.count(), 1)

    @patch("actions_data.operations.demo_data_pusher.time.sleep")
    def test_rotate_token(self, mock_sleep):
        pusher = DemoDataPusher(self.mock_process_webhook_event)
        first_token = pusher.token
        pusher.rotate_token()
        second_token = pusher.token
        self.assertNotEqual(first_token, second_token)
        pusher.rotate_token()
        mock_sleep.assert_called_with(60)  # Initial backoff time

    def test_init_with_no_tokens(self):
        UserSocialAuth.objects.all().delete()
        with self.assertRaises(ValueError):
            DemoDataPusher(self.mock_process_webhook_event)

    def test_init_with_no_orgs(self):
        OwnerEntity.objects.all().delete()
        with self.assertRaises(ValueError):
            DemoDataPusher(self.mock_process_webhook_event)

    @patch("actions_data.operations.demo_data_pusher.logger")
    def test_run_with_exception(self, mock_logger):
        pusher = DemoDataPusher(self.mock_process_webhook_event)
        pusher.push_demo_data_to_webhook_events = MagicMock(
            side_effect=Exception("Test exception")
        )

        pusher.run(timedelta(days=1))

        mock_logger.error.assert_called()

    @patch("actions_data.tasks.process_organization_data.delay")
    def test_push_demo_data_to_webhook_events_task(self, mock_process_org_task):
        """Test that the main task correctly dispatches organization processing tasks"""
        # Execute the task
        started_minutes_ago = 60
        push_demo_data_to_webhook_events(started_minutes_ago)

        # Verify that process_organization_data was called for each fetchable org
        self.assertEqual(mock_process_org_task.call_count, 1)
        expected_calls = [
            call(22552083, started_minutes_ago),
        ]
        mock_process_org_task.assert_has_calls(expected_calls)

    @responses.activate
    @freeze_time("2024-11-11T09:53:23.329544Z")
    @patch("actions_data.tasks.redis")
    @patch("actions_data.tasks.requests_cache")
    def test_process_organization_data(self, mock_requests_cache, mock_redis):
        """Test processing of individual organization data"""
        responses._add_from_file(
            file_path="tests/responses/test_push_demo_data_to_webhook_events.yaml"
        )
        started_minutes_ago = 5
        process_organization_data(22552083, started_minutes_ago)
        self.assertEqual(OwnerEntity.objects.get(id=22552083).repositories.count(), 1)
        self.assertEqual(self.demo_installation.webhook_events.count(), 2)
