"""
Factory classes for creating test instances.

See: https://factoryboy.readthedocs.io/
"""

import factory
import factory.fuzzy
from django.utils.text import slugify

from stave.models import EventStatus
from stave import models

from zoneinfo import ZoneInfo


class LeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.League"

    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Event"

    class Params:
        status_open = factory.Trait(status=EventStatus.OPEN)

    league = factory.SubFactory(LeagueFactory)
    name = factory.Faker("sentence", nb_words=4)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    start_date = factory.Faker("date_between", start_date="+1d", end_date="+30d")
    end_date = factory.Faker(
        "date_between",
        start_date=factory.SelfAttribute("..start_date"),
        end_date="+30d",
    )


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Game"

    event = factory.SubFactory(EventFactory)
    name = factory.Faker("sentence", nb_words=2)
    home_league = factory.Faker("sentence", nb_words=2)
    home_team = factory.Faker("sentence", nb_words=2)
    visiting_league = factory.Faker("sentence", nb_words=2)
    visiting_team = factory.Faker("sentence", nb_words=2)
    association = factory.fuzzy.FuzzyChoice(models.GameAssociation)
    kind = factory.fuzzy.FuzzyChoice(models.GameKind)
    start_time = factory.Faker(
        "date_time_between",
        start_date=factory.SelfAttribute("..event.start_date"),
        end_date=factory.SelfAttribute("..event.end_date"),
        tzinfo=factory.LazyAttribute(
            lambda obj: ZoneInfo(obj.factory_parent.event.league.time_zone)
        ),
    )
    end_time = factory.Faker(
        "date_time_between",
        start_date=factory.SelfAttribute("..start_time"),
        end_date="+2h",
        tzinfo=factory.LazyAttribute(
            lambda obj: ZoneInfo(obj.factory_parent.event.league.time_zone)
        ),
    )
    order_key = 1


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.User"

    preferred_name = factory.Faker("first_name")
    email = factory.Faker("email")
    password = factory.django.Password("password123")  # Default password for all users


class ApplicationFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.ApplicationForm"

    event = factory.SubFactory(EventFactory)
    application_kind = factory.fuzzy.FuzzyChoice(models.ApplicationKind)
    application_availability_kind = factory.fuzzy.FuzzyChoice(
        models.ApplicationAvailabilityKind
    )  # TODO: constrain
    closed = False
    close_date = factory.Faker(
        "date_between",
        start_date=factory.SelfAttribute("..event.start_date"),
        end_date=factory.SelfAttribute("..event.end_date"),
    )
    hidden = False
    intro_text = factory.Faker("sentence", nb_words=20)
    requires_profile_fields = factory.LazyAttribute(
        lambda _: models.User.ALLOWED_PROFILE_FIELDS[:]
    )
    invitation_email_template = None
    schedule_email_template = None
    rejection_email_template = None


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Question"

    application_form = factory.SubFactory(ApplicationFormFactory)
    order_key = factory.Faker("integer")
    content = factory.Faker("sentence", nb_words=5)
    kind = factory.fuzzy.FuzzyChoice(models.QuestionKind)
    options = factory.LazyAttribute(
        lambda obj: (
            []
            if obj.kind
            in [models.QuestionKind.LONG_TEXT, models.QuestionKind.SHORT_TEXT]
            else ["foo", "bar", "spam"]
        )
    )
    allow_other = factory.LazyAttribute(
        lambda obj: (
            factory.Faker("boolean")
            if obj.kind == models.QuestionKind.SELECT_MANY
            else False
        )
    )


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Application"

    user = factory.SubFactory(UserFactory)
    form = factory.SubFactory(ApplicationFormFactory)

    status = models.ApplicationStatus.APPLIED
