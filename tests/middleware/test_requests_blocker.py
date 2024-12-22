from django.test import TestCase


class SecurityScanBlockerMiddlewareTests(TestCase):
    def test_safe_paths(self):
        """Test that normal application paths are allowed"""
        safe_paths = [
            "/",
            "/about",
            "/api/v1/users",
            "/static/css/main.css",
            "/blog/2024/03",
            "/contact-us",
            "/my-admin-page",  # Should not trigger 'administrator' pattern
        ]

        for path in safe_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertNotEqual(
                    response.status_code,
                    403,
                    f"Path {path} was blocked but shouldn't be",
                )

    def test_blocked_paths(self):
        """Test that suspicious paths are blocked"""
        blocked_paths = [
            "/wp-admin",
            "/wp-includes/wlwmanifest.xml",
            "/xmlrpc.php",
            "/.env",
            "/.git/config",
            "/administrator/index.php",
            "/phpmyadmin",
            "/config.php",
            "/wp-content/uploads",
            "/.htaccess",
            "/composer.json",
        ]

        for path in blocked_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(
                    response.status_code, 403, f"Path {path} should be blocked"
                )

    def test_case_variations(self):
        """Test that case variations are caught"""
        blocked_paths = [
            "/WP-ADMIN",
            "/phpMyAdmin",
            "/Administrator",
            "/.ENV",
        ]

        for path in blocked_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(
                    response.status_code, 403, f"Path {path} should be blocked"
                )
