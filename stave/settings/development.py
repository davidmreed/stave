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
if not os.environ.get("EMAIL_BACKEND"):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Allow verbose error pages
DEBUG_PROPAGATE_EXCEPTIONS = True

# Don't use Sentry in development unless explicitly configured
if not os.environ.get("SENTRY_DSN"):
    import sentry_sdk

    sentry_sdk.init(dsn="")  # Disable Sentry

# Disable warnings about HTTPS setting change in development
# See: https://docs.djangoproject.com/en/5.2/ref/settings/#forms-urlfield-assume-https
# TODO: Remove when updated to Django 6.x
filterwarnings(
    "ignore", "The FORMS_URLFIELD_ASSUME_HTTPS transitional setting is deprecated."
)
FORMS_URLFIELD_ASSUME_HTTPS = True
