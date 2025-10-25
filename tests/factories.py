"""
Factory classes for creating test instances.

See: https://factoryboy.readthedocs.io/
"""

import factory
from django.utils.text import slugify


class LeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.League"

    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.User"

    email = factory.Faker("email")
    password = factory.django.Password("password123")  # Default password for all users
