from django.views.generic import TemplateView
from django.http import Http404
from .utils import load_all_posts


class BlogListView(TemplateView):
    template_name = "blog/blog_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["posts"] = load_all_posts()
        return context


class BlogPostView(TemplateView):
    template_name = "blog/blog_post.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = load_all_posts()

        # Find the requested post
        slug = kwargs["slug"]
        try:
            post_index = next(i for i, post in enumerate(posts) if post.slug == slug)
            context["post"] = posts[post_index]

            # Add previous/next posts if they exist
            if post_index > 0:
                context["next_post"] = posts[post_index - 1]
            if post_index < len(posts) - 1:
                context["previous_post"] = posts[post_index + 1]

        except StopIteration:
            raise Http404("Post not found")

        return context
