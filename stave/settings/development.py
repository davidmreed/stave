"""
Development-specific settings.
"""

import os

from .base import *  # noqa
from .base import INSTALLED_APPS, MIDDLEWARE

# Debug mode
DEBUG = True

# Development-specific apps
INSTALLED_APPS += [
    "debug_toolbar",
    "django_extensions",  # Useful development tools like shell_plus
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
    EMAIL_BACKEND = "django.core.email.backends.console.EmailBackend"

# Allow verbose error pages
DEBUG_PROPAGATE_EXCEPTIONS = True

# Don't use Sentry in development unless explicitly configured
if not os.environ.get("SENTRY_DSN"):
    import sentry_sdk

    sentry_sdk.init(dsn="")  # Disable Sentry
