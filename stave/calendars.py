import abc
from datetime import date, datetime, time
from uuid import UUID

from django.db.models import Q, QuerySet
from django.http import (
    HttpRequest,
)
from django.utils.translation import gettext_lazy as _
from django_ical.views import ICalFeed

from . import models


class StaveEventFeed(ICalFeed, abc.ABC):
    @abc.abstractmethod
    def items(self) -> QuerySet[models.Event]: ...

    @abc.abstractmethod
    def title(self, obj) -> str: ...

    @abc.abstractmethod
    def description(self, obj) -> str: ...

    def item_title(self, item: models.Event) -> str:
        return item.name

    def item_description(self, item: models.Event) -> str:
        return item.description

    def item_start_datetime(self, item: models.Event) -> datetime | date:
        if item.games.all():
            return item.games.all()[0].start_time

        return item.start_date

    def item_end_datetime(self, item: models.Event) -> datetime | date:
        if item.games.all():
            return item.games.all()[-1].end_time

        return item.end_date

    def item_location(self, item: models.Event) -> str:
        return item.location


class MyEventsFeed(ICalFeed):
    def title(self, obj: models.User) -> str:
        return _("Stave Events for {user}").format(user=obj)

    def description(self, obj: models.User) -> str:
        return _("Calendar of events applied for and managed by {user}").format(
            user=obj
        )

    def get_object(self, request: HttpRequest, user_id: UUID) -> models.User | None:
        return models.User.objects.filter(id=user_id).first()

    def items(self, obj: models.User) -> QuerySet[models.Event]:
        return (
            (
                models.Event.objects.manageable(obj)
                | models.Event.objects.filter(
                    Q(application_forms__applications__user=obj)
                    & ~Q(
                        application_forms__applications__status=models.ApplicationStatus.REJECTED,
                        application_forms__applications__rejection_email_sent=True,
                    )
                    & ~Q(
                        application_forms__applications__status=models.ApplicationStatus.WITHDRAWN
                    )
                ).distinct()
            )
            .filter(~Q(status=models.EventStatus.CANCELED))
            .distinct()
        )


class LeagueEventsFeed(ICalFeed):
    def get_object(
        self, request: HttpRequest, league_slug: str
    ) -> models.League | None:
        return models.League.objects.filter(slug=league_slug, enabled=True).first()

    def title(self, obj: models.League) -> str:
        return _("Events for {league}").format(league=obj)

    def description(self, obj: models.League) -> str:
        return _("Events for {league}").format(league=obj)

    def items(self, obj: models.League) -> QuerySet[models.Event]:
        return obj.events.listed(None)


class AllEventsFeed(ICalFeed):
    def title(self, obj: models.League) -> str:
        return _("All Stave Events")

    def description(self, obj: models.League) -> str:
        return _("All Stave Events")

    def items(self) -> QuerySet[models.Event]:
        return models.Event.objects.listed(None)
