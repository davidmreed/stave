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
from datetime import time


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

    class Params:
        with_league = factory.Trait(league_template=None)
        with_league_template = factory.Trait(league=None)

    with_league = True
    name = factory.Faker("sentence", nb_words=1)
    event_only = False

    roles = factory.RelatedFactoryList(
        RoleFactory,
        factory_related_name="role_group",
        size=lambda: random.randint(1, 10),
    )
    league = factory.SubFactory("tests.factories.LeagueFactory")
    league_template = factory.SubFactory("tests.factories.LeagueTemplateFactory")


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


class CrewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Crew"

    name = factory.Faker("sentence", nb_words=2)
    event = factory.SubFactory(EventFactory)
    role_group = factory.SubFactory(RoleGroupFactory)
    kind = factory.fuzzy.FuzzyChoice(models.CrewKind)


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
    invitation_email_template = factory.SubFactory(
        "tests.factories.MessageTemplateFactory",
        league=factory.SelfAttribute("..event.league"),
        league_template=None,
    )
    schedule_email_template = factory.SubFactory(
        "tests.factories.MessageTemplateFactory",
        league=factory.SelfAttribute("..event.league"),
        league_template=None,
    )

    rejection_email_template = factory.SubFactory(
        "tests.factories.MessageTemplateFactory",
        league=factory.SelfAttribute("..event.league"),
        league_template=None,
    )

    # TODO: applicationformtemplates
    questions = factory.RelatedFactoryList(
        "tests.factories.QuestionFactory",
        factory_related_name="application_form",
        size=lambda: random.randint(1, 10),
    )


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.Question"

    class Params:
        with_application_form = factory.Trait(application_form_template=None)
        with_application_form_template = factory.Trait(application_form=None)

    with_application_form = True
    application_form = factory.SubFactory(ApplicationFormFactory)
    application_form_template = factory.SubFactory(
        "tests.factories.ApplicationFormTemplateFactory"
    )
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

    # Questions


class LeagueTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.LeagueTemplate"

    name = factory.Faker("sentence", nb_words=2)
    description = factory.Faker("sentence", nb_words=12)


class EventTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.EventTemplate"
        skip_postgeneration_save = True

    class Params:
        single = factory.Trait(days=1, game_templates__per_day=1)
        double = factory.Trait(days=1, game_templates__per_day=2)
        two_day = factory.Trait(days=2, game_templates__per_day=2)

    @factory.post_generation
    def game_templates(obj, create, extracted, **kwargs):
        for day in range(obj.days):
            start_time = time(8, 0, 0)
            for template in range(kwargs.get("per_day", 1)):
                GameTemplateFactory(
                    event_template=obj,
                    day=day,
                    start_time=start_time,
                    end_time=time(start_time.hour + 2, 0, 0),
                )
                start_time = time(start_time.hour + 2, 0, 0)

    league_template = factory.SubFactory(LeagueTemplateFactory)
    name = factory.Faker("sentence", nb_words=2)
    description = factory.Faker("sentence", nb_words=12)
    # application_form_templates = None

    location = factory.Faker("sentence", nb_words=6)


class GameTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.GameTemplate"

    event_template = factory.SubFactory(EventTemplateFactory)
    home_league = factory.Faker("sentence", nb_words=2)
    home_team = factory.Faker("sentence", nb_words=2)
    visiting_league = factory.Faker("sentence", nb_words=2)
    visiting_team = factory.Faker("sentence", nb_words=2)
    association = factory.fuzzy.FuzzyChoice(models.GameAssociation)
    kind = factory.fuzzy.FuzzyChoice(models.GameKind)
    start_time = None
    end_time = None
    day = None


class ApplicationFormTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.ApplicationFormTemplate"
        skip_postgeneration_save = True

    class Params:
        with_league = factory.Trait(league_template=None)
        with_league_template = factory.Trait(league=None)

    with_league = True

    league = factory.SubFactory(LeagueFactory)
    league_template = factory.SubFactory(LeagueTemplateFactory)
    name = factory.Faker("sentence", nb_words=2)

    application_kind = factory.fuzzy.FuzzyChoice(models.ApplicationKind)
    application_availability_kind = factory.fuzzy.FuzzyChoice(
        models.ApplicationAvailabilityKind
    )  # TODO: constrain
    intro_text = factory.Faker("paragraph", nb_sentences=3)
    requires_profile_fields = factory.LazyAttribute(
        lambda _: models.User.ALLOWED_PROFILE_FIELDS[:]
    )
    invitation_email_template = factory.SubFactory(
        "tests.factories.MessageTemplateFactory",
        league_template=factory.SelfAttribute("..league_template"),
        league=factory.SelfAttribute("..league"),
    )
    assigned_email_template = factory.SubFactory(
        "tests.factories.MessageTemplateFactory",
        league_template=factory.SelfAttribute("..league_template"),
        league=factory.SelfAttribute("..league"),
    )
    rejected_email_template = factory.SubFactory(
        "tests.factories.MessageTemplateFactory",
        league_template=factory.SelfAttribute("..league_template"),
        league=factory.SelfAttribute("..league"),
    )

    @factory.post_generation
    def questions(obj, create, extracted, **kwargs):
        for i in range(random.randint(1, 10)):
            QuestionFactory(
                with_application_form_template=True, application_form_template=obj
            )


class ApplicationFormTemplateAssignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.ApplicationFormTemplateAssignment"

    application_form_template = factory.SubFactory(ApplicationFormTemplateFactory)
    event_template = factory.SubFactory(EventTemplateFactory)


class MessageTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.MessageTemplate"

    class Params:
        with_league = factory.Trait(league_template=None)
        with_league_template = factory.Trait(league=None)

    with_league = True
    league_template = factory.SubFactory(LeagueTemplateFactory)
    league = factory.SubFactory(LeagueFactory)
    subject = factory.Faker("sentence", nb_words=8)
    content = factory.Faker("paragraph", nb_sentences=6)
    name = factory.Faker("sentence", nb_words=2)
