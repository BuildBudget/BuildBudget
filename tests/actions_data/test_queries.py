from django.test import TestCase


class TestQueries(TestCase):

    fixtures = [
        "tests/fixtures/authusers.yaml",
        "tests/fixtures/usersocialauths.yaml",
        "tests/fixtures/owners_crowded.yaml",
        "tests/fixtures/repositories_crowded.yaml",
        "tests/fixtures/repository_accesses_crowded.yaml",
    ]
