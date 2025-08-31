import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler.util import close_old_connections

from stave import jobs

logger = logging.getLogger(__name__)


@close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.

    :param max_age: The maximum length of time to retain historical job execution records.
                    Defaults to 7 days.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        _ = scheduler.add_job(
            jobs.delete_old_messages,
            trigger=CronTrigger(day="*"),
            id="delete_old_messages",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'delete_old_messages'.")

        _ = scheduler.add_job(
            jobs.send_emails,
            trigger=CronTrigger(minute="*"),
            id="send_emails",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'send_emails'.")

        _ = scheduler.add_job(
            jobs.update_event_statuses,
            trigger=CronTrigger(hour="*"),
            id="update_event_statuses",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'update_event_statuses'.")

        _ = scheduler.add_job(
            jobs.clean_up_unconfirmed_users,
            trigger=CronTrigger(hour="*"),
            id="clean_up_unconfirmed_users",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'clean_up_unconfirmed_users'.")

        _ = scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),  # Midnight on Monday, before start of the next work week.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added weekly job: 'delete_old_job_executions'.")

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
