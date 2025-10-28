"""
Factory classes for creating test instances.

See: https://factoryboy.readthedocs.io/
"""

import factory
import factory.fuzzy
from django.utils.text import slugify

from stave.models import EventStatus
from stave import models
import random
from zoneinfo import ZoneInfo


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Role"

    order_key = factory.Sequence(lambda n: n)
    role_group = factory.SubFactory("tests.factories.RoleGroupFactory")
    name = factory.Faker("sentence", nb_words=1)
    nonexclusive = False


class RoleGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.RoleGroup"
        skip_postgeneration_save = True

    name = factory.Faker("sentence", nb_words=1)
    event_only = False

    roles = factory.RelatedFactoryList(
        RoleFactory,
        factory_related_name="role_group",
        size=lambda: random.randint(1, 10),
    )
    league = factory.SubFactory("tests.factories.LeagueFactory")


class LeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.League"
        skip_postgeneration_save = True

    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))

    role_groups = factory.RelatedFactoryList(
        RoleGroupFactory,
        factory_related_name="league",
        size=lambda: random.randint(3, 6),
    )


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
        skip_postgeneration_save = True

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
    intro_text = factory.Faker("paragraph", nb_sentences=3)
    requires_profile_fields = factory.LazyAttribute(
        lambda _: models.User.ALLOWED_PROFILE_FIELDS[:]
    )
    invitation_email_template = None
    schedule_email_template = None
    rejection_email_template = None

    questions = factory.RelatedFactoryList(
        "tests.factories.QuestionFactory",
        factory_related_name="application_form",
        size=lambda: random.randint(1, 10),
    )


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Question"

    application_form = factory.SubFactory(ApplicationFormFactory)
    order_key = factory.Sequence(lambda n: n)
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
            bool(random.randint(0, 1))
            if obj.kind == models.QuestionKind.SELECT_MANY
            else False
        )
    )


class ApplicationResponseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.ApplicationResponse"

    application = factory.SubFactory("tests.factories.ApplicationFactory")
    question = factory.SubFactory(QuestionFactory)
    content = factory.Faker("sentence", nb_words=6)


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Application"

    user = factory.SubFactory(UserFactory)
    form = factory.SubFactory(ApplicationFormFactory)

    status = models.ApplicationStatus.APPLIED

    # Roles
