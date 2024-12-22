from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User


class ImpersonationMixin(UserPassesTestMixin):

    def get_owner(self, request) -> User:
        # Get user ID from URL component
        user_id = request.resolver_match.kwargs.get("user_id")
        user = User.objects.get(id=user_id)
        return user

    def test_func(self):
        return self.request.user.is_superuser
