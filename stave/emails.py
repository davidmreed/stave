from . import models
from django.urls import reverse_lazy
import re
from markdownify.templatetags.markdownify import markdownify

FOOTER_MD = f"""

--<br>
Sent by [Stave](https://stave.app{reverse_lazy("home")}) in response to your application | [Manage Your Account](https://stave.app{reverse_lazy("profile")})
"""
MERGE_FIELD_PATTERN = re.compile(r"\{([a-zA-Z\._]+?)\}")
MD_LINK_PATTERN = re.compile(r"\[([^\]]+?)\]\(([^)]+?)\)")
LINE_BREAK_PATTERN = re.compile(r"<br( /)?>")


def substitute(
    context: models.MergeContext,
    content: str,
) -> str:
    # Substitute values for any of the user's tags.
    return MERGE_FIELD_PATTERN.sub(
        lambda match: (context.get_merge_field_value(match.group(1)) or match.group()),
        content,
    )


def render_html(content: str) -> str:
    return markdownify(content)


def render_txt(content: str) -> str:
    # Just return the Markdown source, but make the links and line-breaks more usable.
    return MD_LINK_PATTERN.sub(
        lambda match: f"{match.group(1)} ({match.group(2)})",
        LINE_BREAK_PATTERN.sub(
            lambda match: "\n",
            content,
        ),
    )


def send_message_from_messagetemplate(
    application: models.Application,
    sender: models.User | None,
    kind: models.SendEmailContextType,
):
    message_template = application.form.get_template_for_context_type(kind)
    send_message(
        application, sender, kind, message_template.subject, message_template.content
    )


def send_message(
    application: models.Application,
    sender: models.User | None,
    kind: models.SendEmailContextType | None,
    subject: str,
    content: str,
):
    context = models.MergeContext(
        league=application.form.event.league,
        event=application.form.event,
        app_form=application.form,
        application=application,
        user=application.user,
        sender=sender,
    )

    content = content + FOOTER_MD

    message = models.Message(
        subject=render_txt(substitute(context, subject)),
        content_plain_text=render_txt(substitute(context, content)),
        content_html=render_html(substitute(context, content)),
        user=application.user,
    )
    message.save()

    # TODO: this logic probably belongs elsewhere.
    match kind:
        case models.SendEmailContextType.INVITATION:
            application.status = models.ApplicationStatus.INVITED
        case models.SendEmailContextType.REJECTION:
            application.status = models.ApplicationStatus.REJECTED
            # Remove any assignments for this user.
            models.CrewAssignment.objects.filter(
                user=application.user,
                crew__event=application.form.event,
                role__in=application.roles.all(),
            ).delete()
        case models.SendEmailContextType.SCHEDULE:
            application.status = models.ApplicationStatus.ASSIGNED

    application.save()
