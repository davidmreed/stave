from pytest_factoryboy import register

from tests import factories

# See: https://pytest-factoryboy.readthedocs.io/
register(factories.UserFactory)
