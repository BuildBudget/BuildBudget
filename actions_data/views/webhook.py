import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from actions_data.models import WebhookEvent, UserProfile
from actions_data.tasks import process_webhook_event


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = json.loads(request.body)
        headers = request.headers
        user_id = request.GET.get("user")
        created_event = WebhookEvent.objects.create_from_headers_and_payload(
            headers=headers, payload=payload, user_id=user_id
        )
        process_webhook_event.delay(created_event.id)
        return HttpResponse(status=200)
