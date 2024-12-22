from django.urls import path
from .views import BlogListView, BlogPostView

app_name = "blog"

urlpatterns = [
    path("", BlogListView.as_view(), name="blog_list"),
    path("<slug:slug>/", BlogPostView.as_view(), name="blog_post"),
]
