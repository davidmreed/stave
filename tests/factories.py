"""
Factory classes for creating test instances.

See: https://factoryboy.readthedocs.io/
"""

import factory
from django.utils.text import slugify

from stave.models import EventStatus


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


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.User"

    email = factory.Faker("email")
    password = factory.django.Password("password123")  # Default password for all users
