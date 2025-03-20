from django.core.management.base import BaseCommand
from stave.jobs import app


class Command(BaseCommand):
    help = "Setup the periodic tasks runner"

    def handle(self, *args, **options):
        app.run()
