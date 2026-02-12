import abc
from datetime import date, datetime
from uuid import UUID

from django.db.models import QuerySet
from django.http import (
    HttpRequest,
)
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django_ical.views import ICalFeed

from . import models


class StaveEventFeed(ICalFeed, abc.ABC):
    product_id = "-//stave.app//Stave//EN"

    @abc.abstractmethod
    def items(self) -> QuerySet[models.Event]: ...

    @abc.abstractmethod
    def title(self, obj) -> str: ...

    @abc.abstractmethod
    def description(self, obj) -> str: ...

    def item_title(self, item: models.Event) -> str:
        return item.name

    def item_description(self, item: models.Event) -> str:
        return item.name

    def item_start_datetime(self, item: models.Event) -> datetime | date:
        if item.games.all():
            return item.games.all()[0].start_time

        return item.start_date

    def item_end_datetime(self, item: models.Event) -> datetime | date:
        if item.games.all():
            return list(item.games.all())[-1].end_time

        return item.end_date

    def item_location(self, item: models.Event) -> str:
        return item.location


class MyEventsFeed(StaveEventFeed):
    def title(self, obj: models.User) -> str:
        return _("Stave Events for {user}").format(user=obj)

    def description(self, obj: models.User) -> str:
        return _(
            "Calendar of events applied for and managed by {user} on Stave.app"
        ).format(user=obj)

    def get_object(self, request: HttpRequest, user_id: UUID) -> models.User:
        return get_object_or_404(models.User, id=user_id)

    def items(self, obj: models.User) -> QuerySet[models.Event]:
        applications = models.Application.objects.filter(
            user=obj,
        ).exclude(
            status__in=[
                models.ApplicationStatus.REJECTED,
                models.ApplicationStatus.WITHDRAWN,
            ]
        )

        return (
            (
                models.Event.objects.manageable(obj)
                | models.Event.objects.filter(
                    application_forms__applications__id__in=applications
                ).distinct()
            )
            .exclude(status=models.EventStatus.CANCELED)
            .distinct()
            .prefetch_for_display()
        )


class LeagueEventsFeed(StaveEventFeed):
    def get_object(self, request: HttpRequest, league_slug: str) -> models.League:
        return get_object_or_404(
            models.League.objects.filter(enabled=True), slug=league_slug
        )

    def title(self, obj: models.League) -> str:
        return _("Stave Events for {league}").format(league=obj)

    def description(self, obj: models.League) -> str:
        return _("Events for {league} from Stave.app").format(league=obj)

    def items(self, obj: models.League) -> QuerySet[models.Event]:
        return obj.events.listed(None).prefetch_for_display()


class LeagueGroupEventsFeed(StaveEventFeed):
    def get_object(self, request: HttpRequest, id: UUID) -> models.LeagueGroup:
        return get_object_or_404(models.LeagueGroup.objects.all(), id=id)

    def title(self, obj: models.LeagueGroup) -> str:
        return _("Stave Events for {league_group}").format(league_group=obj)

    def description(self, obj: models.LeagueGroup) -> str:
        return _("Events for {league_group} from Stave.app").format(league_group=obj)

    def items(self, obj: models.LeagueGroup) -> QuerySet[models.Event]:
        return (
            models.Event.objects.listed(None)
            .in_league_group(obj)
            .prefetch_for_display()
        )


class MySubscriptionsEventFeed(StaveEventFeed):
    def get_object(self, request: HttpRequest, user_id: UUID) -> models.User:
        return get_object_or_404(models.User.objects.all(), id=user_id)

    def title(self, obj: models.User) -> str:
        return _("Stave Events for {user} Subscriptions").format(user=obj)

    def description(self, obj: models.LeagueGroup) -> str:
        return _("Events for {user} Subscriptions from Stave.app").format(user=obj)

    def items(self, obj: models.User) -> QuerySet[models.Event]:
        return models.Event.objects.subscribed(obj).prefetch_for_display()


class AllEventsFeed(StaveEventFeed):
    def title(self, obj: models.League) -> str:
        return _("All Stave Events")

    def description(self, obj: models.League) -> str:
        return _("All events from Stave.app")

    def items(self) -> QuerySet[models.Event]:
        return models.Event.objects.listed(None).prefetch_for_display()
