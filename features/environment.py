import os

BEHAVE_DEBUG_ON_ERROR = False


def setup_debug_on_error(userdata):
    global BEHAVE_DEBUG_ON_ERROR
    BEHAVE_DEBUG_ON_ERROR = userdata.getbool("BEHAVE_DEBUG_ON_ERROR")


def before_all(context):
    # Set Django settings for testing - behave_django will handle Django setup
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stave.settings.development")
    setup_debug_on_error(context.config.userdata)


def after_step(context, step):
    if BEHAVE_DEBUG_ON_ERROR and step.status == "failed":
        import sys
        import pdb

        old_stdout = sys.stdout
        sys.stdout = sys.__stdout__
        try:
            pdb.post_mortem(step.exc_traceback)
        finally:
            sys.stdout = old_stdout
