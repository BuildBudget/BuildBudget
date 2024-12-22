from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("actions_data.urls")),
    path("admin/", admin.site.urls),
    path("", include("social_django.urls", namespace="social")),
    # ... your existing urls
    path("blog/", include("blog.urls")),
]
