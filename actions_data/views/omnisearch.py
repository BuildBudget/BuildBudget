from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views import View
from django.http import JsonResponse
from django.db.models import Q

from actions_data.models import Workflow, Repository, OwnerEntity


class BaseOmnisearchView(View):
    def get_owner(self):
        pass

    def serialize_results(self, objects, object_type):
        """Serialize a queryset of objects into a list of dictionaries."""
        return [
            {
                "id": f"{object_type}_{obj.id}",
                "type": object_type,
                "name": obj.get_full_name(),
                "url": obj.get_absolute_url(),
            }
            for obj in objects
        ]

    def get_workflows(self, query):
        return Workflow.objects.filter_for_user(self.get_owner()).filter(
            Q(name__icontains=query) | Q(path__icontains=query)
        )[:5]

    def get_repositories(self, query):
        return Repository.objects.filter_for_user(self.get_owner()).filter(
            name__icontains=query
        )[:5]

    def get_owner_entities(self, query):
        return OwnerEntity.objects.filter_for_user(self.get_owner()).filter(
            login__icontains=query
        )[:5]

    def get(self, request, *args, **kwargs):
        # Get and validate query parameter
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse([], safe=False)

        # Get results from each model
        results = []

        # OwnerEntities
        owner_entities = self.get_owner_entities(query)
        results.extend(self.serialize_results(owner_entities, "org"))

        # Repositories
        repositories = self.get_repositories(query)
        results.extend(self.serialize_results(repositories, "repo"))

        # Workflows
        workflows = self.get_workflows(query)
        results.extend(self.serialize_results(workflows, "workflow"))

        return JsonResponse(results, safe=False)


class OmniSearchView(LoginRequiredMixin, BaseOmnisearchView):

    def get_owner(self):
        return self.request.user


class DemoOmnisearchView(BaseOmnisearchView):
    def get_owner(self):
        return User.objects.get(username=settings.DEMO_USERNAME)

    def serialize_results(self, objects, object_type):
        """Serialize a queryset of objects into a list of dictionaries."""
        return [
            {
                "id": f"{object_type}_{obj.id}",
                "type": object_type,
                "name": obj.get_full_name(),
                "url": obj.get_demo_url(),
            }
            for obj in objects
        ]
