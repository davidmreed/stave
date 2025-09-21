"""
Production-specific settings.
"""

from .base import *  # noqa

# Security settings
DEBUG = False

# Production static files storage with compression and hashing
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
