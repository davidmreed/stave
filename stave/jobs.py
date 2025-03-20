from . import models, settings
from datetime import datetime, timedelta, timezone
from django.core.mail import EmailMultiAlternatives
from rocketry import Rocketry

app = Rocketry(execution="main")


@app.task("every minute")
def send_emails():
    for message in models.Message.objects.filter(
        sent=False, tries__lt=settings.STAVE_EMAIL_MAX_TRIES
    ):
        try:
            email = EmailMultiAlternatives(
                subject=message.subject,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=message.user.email,
                body=message.content_plain_text,
            )
            email.attach_alternative(message.content_html, "text/html")

            _ = email.send()
        except Exception:
            message.tries += 1
        else:
            message.sent_date = datetime.now(tz=timezone.utc)
            message.sent = True

        message.save()


@app.task("every day")
def delete_old_messages():
    _ = models.Message.objects.filter(
        sent=True, send_date__leq=datetime.now(tz=timezone.utc) - timedelta(days=7)
    ).delete()


@app.task("every hour")
def update_event_statuses():
    # These are date-based, not hour-based - TODO
    _ = models.Event.objects.filter(
        status__in=[models.EventStatus.LINK_ONLY, models.EventStatus.OPEN],
        start_date__leq=datetime.now(tz=timezone.utc),
    ).update(status=models.EventStatus.IN_PROGRESS)

    _ = models.Event.objects.filter(
        status=models.EventStatus.IN_PROGRESS,
        end_date__leq=datetime.now(tz=timezone.utc),
    ).update(status=models.EventStatus.COMPLETE)
