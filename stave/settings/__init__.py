"""
Settings module that loads the appropriate configuration based on environment.
"""

import os

# Determine which settings module to use based on DJANGO_ENV
env = os.environ.get("DJANGO_ENV", "development")

if env == "production":  # pragma: no cover
    from .production import *  # noqa
elif env == "development":  # pragma: no cover
    from .development import *  # noqa
else:  # pragma: no cover
    raise ValueError(
        f"Unknown DJANGO_ENV: {env}. Must be 'development' or 'production'"
    )
