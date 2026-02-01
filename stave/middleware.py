import logging


class LocaleRewriteMiddleware:
    """
    This class is a middleware that rewrites `request.LANGUAGE_CODE` value of 'en'  to 'en-us' so it doesn't  produce
    log messages.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, get_response):
        self.logger.info("LocaleRewriteMiddleware initialized")
        self.get_response = get_response

    def __call__(self, request):
        if request.LANGUAGE_CODE not in {"en-us", "es"}:
            self.logger.warning(
                f'Language {request.LANGUAGE_CODE} does not have a translation yet. Defaulting to "en-us".'
            )
            request.LANGUAGE_CODE = "en-us"
        response = self.get_response(request)
        return response
