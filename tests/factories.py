"""
Factory classes for creating test instances.

See: https://factoryboy.readthedocs.io/
"""

import factory
from faker import Factory as FakerFactory


faker = FakerFactory.create()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "stave.User"

    email = factory.LazyAttribute(lambda x: faker.email())
    password = factory.django.Password("password123")  # Default password for all users
