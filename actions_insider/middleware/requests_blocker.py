from django.http import HttpResponseForbidden
import re


class SecurityScanBlockerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # Common scan patterns
        patterns = [
            r"wp-(?:admin|content|includes)",  # WordPress paths
            r"xmlrpc\.php",  # WordPress XML-RPC
            r"\.env",  # Environment files
            r"\.git",  # Git repository
            r"\.sql",  # SQL files
            r"composer\.json",  # PHP related
            r"config\.php",  # PHP configs
            r"\.htaccess",  # Apache config
            r"administrator",  # Common admin paths
            r"\.asp",  # ASP files
            r"\.php",  # PHP files
            r"phpmyadmin",  # phpMyAdmin paths
        ]

        # Compile pattern - case insensitive
        self.pattern = re.compile("(?i)" + "|".join(patterns))

    def __call__(self, request):
        # Let Django handle path normalization, then check the normalized path
        if self.pattern.search(request.path):
            return HttpResponseForbidden("Access Denied")

        return self.get_response(request)
