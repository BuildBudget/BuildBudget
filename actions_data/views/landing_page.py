from django.shortcuts import redirect, render
from django.views.generic import View, TemplateView


class LandingPageView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("stats_by_workflow")
        return render(request, "actions_data/landing_page.html")


class AboutPageView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "actions_data/about.html")
