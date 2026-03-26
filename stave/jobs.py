import logging
from datetime import datetime, timedelta, timezone

import allauth.account.models
from django.core.mail import EmailMultiAlternatives
from django_apscheduler.util import close_old_connections
from django.db import transaction
from . import models, settings, emails


@close_old_connections
def send_emails():
    for message in models.Message.objects.filter(
        sent=False, tries__lt=settings.STAVE_EMAIL_MAX_TRIES
    ):
        try:
            email = EmailMultiAlternatives(
                subject=message.subject,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[message.user.email if message.user else message.email],
                body=message.content_plain_text,
            )
            if message.reply_to:
                email.reply_to = [message.reply_to]

            email.attach_alternative(message.content_html, "text/html")

            email.send()
        except Exception as e:
            logging.getLogger().error(f"Could not send message {message}: {e}")
            message.tries += 1
        else:
            message.sent_date = datetime.now(tz=timezone.utc)
            message.sent = True

        message.save()


@close_old_connections
def delete_old_messages():
    models.Message.objects.filter(
        sent=True, sent_date__lte=datetime.now(tz=timezone.utc) - timedelta(days=7)
    ).delete()


@close_old_connections
def update_event_statuses():
    # These are date-based, not hour-based - TODO
    models.Event.objects.filter(
        status__in=[models.EventStatus.LINK_ONLY, models.EventStatus.OPEN],
        start_date__lte=datetime.now(tz=timezone.utc),
    ).update(status=models.EventStatus.IN_PROGRESS)

    models.Event.objects.filter(
        status=models.EventStatus.IN_PROGRESS,
        end_date__lt=datetime.now(tz=timezone.utc),
    ).update(status=models.EventStatus.COMPLETE)


@close_old_connections
def clean_up_unconfirmed_users():
    deleted = (
        models.User.objects.filter(
            date_created__lt=datetime.now(tz=timezone.utc) - timedelta(days=7)
        )
        .exclude(
            id__in=allauth.account.models.EmailAddress.objects.filter(
                verified=True
            ).values_list("user")
        )
        .delete()
    )
    logging.info(f"Deleted {deleted} unconfirmed accounts")


@close_old_connections
def send_reminder_emails():
    for email_type in [emails.LeagueUserInvitationReminder]:
        with transaction.atomic():
            email_type_instance = email_type()
            for item in email_type_instance.get_queryset().select_for_update():
                if email_type_instance.is_due(item):
                    (subj, content, destination) = email_type_instance.get_message(item)
                    emails.send_message_with_content(
                        subj,
                        content,
                        destination,
                    )
                    email_type_instance.update_for_message_sent(item)


@close_old_connections
def expire_league_user_invitations():
    # League user invitations are valid for seven days.
    # We message users every three days, that is, on days 0, 3, and 6.
    # On day 7, we expire the invitation.
    with transaction.atomic():
        for invitation in models.LeagueUserInvitation.objects.filter(
            status=models.LeagueUserInvitationStatus.OPEN,
            expiration_date__lt=datetime.now(tz=timezone.utc),
        ).select_for_update():
            invitation.status = models.LeagueUserInvitationStatus.EXPIRED
            invitation.save()
