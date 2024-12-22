import responses
from django.test import SimpleTestCase

from actions_data.github_client import (
    get_github_orgs_and_repos_with_app_installed,
)


class TestGitHubClient(SimpleTestCase):

    @responses.activate
    def test_get_github_orgs_and_repos_with_app_installed(self):
        responses._add_from_file(
            file_path="tests/responses/test_get_github_orgs_as_admin.yaml"
        )
        token = "token"
        result = get_github_orgs_and_repos_with_app_installed(token)

        self.assertEqual(len(result), 4)

        # Check first org (eduramirezh)
        edu_org = result[1]
        self.assertEqual(edu_org.org.login, "eduramirezh")

        # Sample some expected repositories for eduramirezh
        expected_edu_repos = {
            "eduramirezh/5etools_ebook_parser",
            "eduramirezh/backstage",
            "eduramirezh/git-history",
            "eduramirezh/zeit",  # last repo in the list
        }
        actual_edu_repos = {repo.repo.full_name for repo in edu_org.user_repos}
        for repo in expected_edu_repos:
            pass
            self.assertIn(
                repo, actual_edu_repos, f"Missing expected repository: {repo}"
            )

        # Check second org (BuildBudget)
        build_org = result[2]
        self.assertEqual(build_org.org.login, "BuildBudget")

        # Check the single repo for BuildBudget
        self.assertEqual(len(build_org.user_repos), 1)
        self.assertEqual(
            build_org.user_repos[0].repo.full_name, "BuildBudget/hello-world"
        )
