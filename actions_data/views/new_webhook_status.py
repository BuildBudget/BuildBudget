from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View


class NewWebhookStatusView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        reference_time = request.GET.get("reference_time")
        if not reference_time:
            return JsonResponse({"error": "No reference time provided"}, status=400)

        try:
            reference_datetime = datetime.fromisoformat(reference_time)
        except ValueError:
            return JsonResponse({"error": "Invalid reference time format"}, status=400)

        # Check for webhooks created after the reference time
        new_installations = request.user.installations.filter(
            created_at__gt=reference_datetime
        )

        if new_installations.exists():
            latest_installation = new_installations.latest("created_at")
            return JsonResponse(
                {
                    "verified": True,
                    "new_webhook": {
                        "webhook_id": latest_installation.webhook_id,
                        "enterprise_host": latest_installation.enterprise_host,
                    },
                }
            )
        else:
            return JsonResponse({"verified": False, "new_webhook": None})
