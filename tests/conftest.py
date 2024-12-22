from collections.abc import Iterable

from django.core.serializers import deserialize, serialize
from django.db.models import QuerySet


def load_additional_fixtures(fixture_names: list[str]):
    for fixture_name in fixture_names:
        with open(f"tests/fixtures/{fixture_name}") as f:
            data = f.read()
            fixture = deserialize("yaml", data)
            for instance in fixture:
                instance.save()


def serialize_collection(query_set: Iterable, fixture_file_name: str):
    with open("tests/fixtures/" + fixture_file_name, "w") as f:
        data = serialize("yaml", query_set)
        f.write(data)
