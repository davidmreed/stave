"""
Tests for database models, using Factories

These tests create model instances via factories without specifying any fields,
to ensure that default values and optional fields are handled correctly.
"""

import datetime
import uuid

import pytest


@pytest.mark.django_db
def test_event_model_creation(event_factory):
    """Create an event via factory and verify its fields."""
    event = event_factory.create()

    assert isinstance(event.id, uuid.UUID)
    assert event.league is not None
    assert event.status.label == "Drafting"

    assert isinstance(event.name, str)
    assert isinstance(event.slug, str)
    assert isinstance(event.start_date, datetime.date)
    assert isinstance(event.end_date, datetime.date)
    assert event.start_date <= event.end_date
    assert event.location == ""

    # Model methods
    assert str(event) == event.name
    assert event.get_absolute_url() == f"/_/{event.league.slug}/events/{event.slug}/"


@pytest.mark.django_db
def test_league_model_creation(league_factory):
    """Create a league via factory and verify its fields."""
    league = league_factory.create()

    assert isinstance(league.id, uuid.UUID)
    assert isinstance(league.name, str)
    assert isinstance(league.slug, str)

    # Default properties
    assert league.enabled is False

    # Model methods
    assert str(league) == league.name
    assert league.get_absolute_url() == f"/_/{league.slug}/"


@pytest.mark.django_db
def test_user_model_creation(user_factory):
    """Create a user via factory and verify its fields."""
    user = user_factory.create()

    # Database columns, in order of appearance in the table
    assert isinstance(user.password, str)
    assert user.last_login is None
    assert isinstance(user.email, str)
    assert isinstance(user.id, uuid.UUID)
    assert isinstance(user.preferred_name, str)
    assert user.pronouns is None
    assert user.game_history_url is None
    assert user.nso_certification_level is None
    assert user.so_certification_level is None
    assert user.mrda_recognized_official is None
    assert user.legal_name is None
    assert user.league_affiliation == "Independent"
    assert user.is_superuser is False
    assert user.is_staff is False
    assert user.insurance is None
    assert isinstance(user.date_created, datetime.datetime)

    assert user.league_permissions.count() == 0

    # Model methods
    assert str(user) == user.preferred_name
    assert user.has_perm("any_permission") is True
    assert user.has_module_perms("any_module") is True
