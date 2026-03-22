from collections import ABC
from datetime import datetime, timedelta
import re

from django.db import QuerySet
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext
from markdownify.templatetags.markdownify import markdownify

from . import models

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
        lambda match: context.get_merge_field_value(match.group(1)) or match.group(),
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
    reply_to: str | None = None,
):
    message_template = application.form.get_template_for_context_type(kind)
    if message_template:
        send_message(
            application,
            sender,
            kind,
            message_template.subject,
            message_template.content,
            reply_to,
        )


def send_message_with_content(
    subject: str,
    content: str,
    destination: models.User | str,
    reply_to: str,
):
    models.Message.objects.create(
        subject=render_txt(subject),
        content_plain_text=render_txt(content),
        content_html=render_html(content),
        user=destination if isinstance(models.User, destination) else None,
        email=destination if isinstance(str, destination) else None,
        reply_to=reply_to,
    )


def send_message(
    application: models.Application,
    sender: models.User | None,
    kind: models.SendEmailContextType | None,
    subject: str,
    content: str,
    reply_to: str | None = None,
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

    final_reply_to = reply_to
    if sender and not final_reply_to:
        final_reply_to = sender.email

    send_message_with_content(
        subject=substitute(context, subject),
        content=substitute(context, content),
        user=application.user,
        reply_to=final_reply_to,
    )

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


class ReminderEmail[T](ABC):
    def get_queryset(self) -> QuerySet[T]: ...

    def get_message(self, item: T) -> (str, str, str): ...

    def is_due(self, item: T) -> bool: ...

    def update_for_sent_message(self, item: T) -> None: ...


class LeagueUserInvitationReminder(ReminderEmail[models.LeagueUserInvitation]):
    def get_queryset(self) -> QuerySet[models.LeagueUserInvitation]:
        return models.LeagueUserInvitation.objects.filter(
            status=models.LeagueUserInvitationStatus.OPEN
        )

    def get_message(self, item: models.LeagueUserInvitation) -> (str, str, str):
        return (
            gettext("Invitation to manage {league} on Stave").format(
                league=item.league
            ),
            gettext(
                "You've been invited to manage {league} on Stave. "
                "To accept or decline this invitation, [click here]"
                "({link}). "
                "Please don't reply to this message. It is not monitored."
            ).format(
                league=item.league,
                link=reverse("league-permission-invite-respond", args=[item.id]),
            ),
            item.email,
        )

    def is_due(self, item: models.LeagueUserInvitation) -> bool:
        return not item.date_last_message_sent or (
            datetime.now() - item.date_last_message_sent
        ) >= timedelta(hours=72)

    def update_for_message_sent(self, item: models.LeagueUserInvitation) -> None:
        item.last_message_sent_date = datetime.now()
        item.save()
