"""
Settings module that loads the appropriate configuration based on environment.
"""

import os

# Determine which settings module to use based on DJANGO_ENV
env = os.environ.get("DJANGO_ENV", "development")

if env == "production":
    from .production import *  # noqa
elif env == "development":
    from .development import *  # noqa
else:
    raise ValueError(
        f"Unknown DJANGO_ENV: {env}. Must be 'development' or 'production'"
    )
