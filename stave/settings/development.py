"""
Development-specific settings.
"""

import os
from warnings import filterwarnings

from .base import *  # noqa
from .base import INSTALLED_APPS, MIDDLEWARE

# Debug mode
DEBUG = True

# Development-specific apps
INSTALLED_APPS += [
    "debug_toolbar",
    "django_extensions",  # Useful development tools like shell_plus
    "behave_django",  # BDD testing framework
]

# Add debug toolbar middleware at the beginning for development
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

# Debug toolbar configuration
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# Development email backend - Use console backend for local development
if not os.environ.get("EMAIL_BACKEND"):  # pragma: no cover
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Allow verbose error pages
DEBUG_PROPAGATE_EXCEPTIONS = True

# Speed up password hashing in development/testing (don't use this in production!)
# Any time the factory creates a user with a password,
# it will be hashed using MD5, which is much faster than the default PBKDF2.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Don't use Sentry in development unless explicitly configured
if not os.environ.get("SENTRY_DSN"):  # pragma: no cover
    import sentry_sdk

    sentry_sdk.init(dsn="")  # Disable Sentry

# Disable warnings about HTTPS setting change in development
# See: https://docs.djangoproject.com/en/5.2/ref/settings/#forms-urlfield-assume-https
# TODO: Remove when updated to Django 6.x
filterwarnings(
    "ignore", "The FORMS_URLFIELD_ASSUME_HTTPS transitional setting is deprecated."
)
FORMS_URLFIELD_ASSUME_HTTPS = True

# File storage
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
