from . import models
from stave.management.commands.create_templates import create_templates
import random
from datetime import datetime, date, time
from django.contrib.auth.models import AnonymousUser

import zoneinfo
import pytest


@pytest.fixture
def base_template(db) -> models.LeagueTemplate:
    return create_templates()


@pytest.fixture
def enabled_league(base_template):
    return base_template.clone(
        name=f"{random.randint(0, 100000)} Roller Derby",
        location="Ceres Station, The Belt",
        description="The **best** roller derby in the Belt and Outer Planets",
        website="https://derby.ceres.belt",
        enabled=True,
    )


@pytest.fixture
def tournament_template(enabled_league):
    return models.EventTemplate.objects.get(league=enabled_league, name="Tournament")


@pytest.fixture
def timezone(enabled_league):
    return zoneinfo.ZoneInfo(enabled_league.time_zone)


@pytest.fixture
def role_group_nso(enabled_league):
    return enabled_league.role_groups.get(name="NSO")


@pytest.fixture
def role_group_so(enabled_league):
    return enabled_league.role_groups.get(name="SO")


@pytest.fixture
def role_group_tho(enabled_league):
    return enabled_league.role_groups.get(name="THO")


@pytest.fixture
def tournament(tournament_template, enabled_league):
    tournament = tournament_template.clone(
        name="Outer Planets Throwdown",
        status=models.EventStatus.OPEN,
        slug="outer-planets-throwdown",
        start_date=date(2218, 5, 25),
        end_date=date(2218, 5, 26),
        location="Ceres Station Level 6",
    )
    tournament_game_1 = models.Game.objects.create(
        event=tournament,
        name="Game 1",
        home_league="Ceres Roller Derby",
        home_team="Miners",
        visiting_league="Ganymede",
        visiting_team="Green Sprouts",
        association=models.GameAssociation.WFTDA,
        kind=models.GameKind.REG,
        start_time=datetime.combine(tournament.start_date, time(10, 00), timezone),
        end_time=datetime.combine(tournament.start_date, time(12, 00), timezone),
        order_key=1,
    )
    tournament_game_2 = models.Game.objects.create(
        event=tournament,
        name="Game 2",
        home_league="Tycho Station",
        home_team="Gearheads",
        visiting_league="Rockhoppers",
        visiting_team="All Stars",
        association=models.GameAssociation.WFTDA,
        kind=models.GameKind.REG,
        start_time=datetime.combine(tournament.start_date, time(12, 00), timezone),
        end_time=datetime.combine(tournament.start_date, time(14, 00), timezone),
        order_key=2,
    )
    tournament_game_3 = models.Game.objects.create(
        event=tournament,
        name="Game 3",
        home_league="Ceres Roller Derby",
        home_team="Nuggets",
        visiting_league="Pallas Station",
        visiting_team="Thin Airs",
        association=models.GameAssociation.JRDA,
        kind=models.GameKind.REG,
        start_time=datetime.combine(tournament.start_date, time(16, 00), timezone),
        end_time=datetime.combine(tournament.start_date, time(18, 00), timezone),
        order_key=3,
    )
    tournament_game_4 = models.Game.objects.create(
        event=tournament,
        name="Game 4",
        home_league="Ceres Roller Derby",
        home_team="Miners",
        visiting_league="Tycho Station",
        visiting_team="Gearheads",
        association=models.GameAssociation.WFTDA,
        kind=models.GameKind.REG,
        start_time=datetime.combine(tournament.end_date, time(12, 00), timezone),
        end_time=datetime.combine(tournament.end_date, time(14, 00), timezone),
        order_key=4,
    )
    tournament_game_5 = models.Game.objects.create(
        event=tournament,
        name="Game 5",
        home_league="Ganymede",
        home_team="Green Sprouts",
        visiting_league="Rockhoppers",
        visiting_team="All Stars",
        association=models.GameAssociation.WFTDA,
        kind=models.GameKind.REG,
        start_time=datetime.combine(tournament.end_date, time(14, 00), timezone),
        end_time=datetime.combine(tournament.end_date, time(16, 00), timezone),
        order_key=5,
    )

    for game in [
        tournament_game_1,
        tournament_game_2,
        tournament_game_3,
        tournament_game_4,
        tournament_game_5,
    ]:
        for role_group in [role_group_so, role_group_nso]:
            _ = models.RoleGroupCrewAssignment.objects.create(
                game=game, role_group=role_group
            )

    ## Create application forms for the tournament
    app_form = tournament.application_forms.filter(slug="apply-nso-so").first()
    app_form.intro_text = "Join the best teams in the Belt! **For beltalowda!**"
    app_form.requires_profile_fields = ["preferred_name"]
    app_form.save()

    models.Question.objects.create(
        application_form=app_form,
        content="What is your affiliated faction?",
        kind=models.QuestionKind.SELECT_ONE,
        options=["Golden Bough", "OPA", "Free Navy"],
        required=True,
        order_key=1,
    )
    models.Question.objects.create(
        application_form=app_form,
        content="What kinds of kibble do you like?",
        kind=models.QuestionKind.SELECT_MANY,
        options=["red", "blue", "green"],
        allow_other=True,
        required=True,
        order_key=2,
    )
    models.Question.objects.create(
        application_form=app_form,
        content="What are your special skills?",
        kind=models.QuestionKind.LONG_TEXT,
        order_key=3,
    )
    models.Question.objects.create(
        application_form=app_form,
        content="What do you think of Marco Inaros?",
        kind=models.QuestionKind.SHORT_TEXT,
        order_key=4,
    )

    app_form_tho = models.ApplicationForm.objects.get(
        event=tournament,
        slug="apply-tho",
    )
    app_form_tho.intro_text = (
        "Join the best teams in the Belt as a tournament leader. **For beltalowda!**"
    )
    app_form_tho.requires_profile_fields = ["preferred_name"]
    app_form_tho.save()

    models.Question.objects.create(
        application_form=app_form_tho,
        content="What do you want to do?",
        kind=models.QuestionKind.LONG_TEXT,
        required=True,
        order_key=1,
    )

    return tournament


@pytest.fixture
def league_manager_user(enabled_league):
    user = models.User.objects.create(
        password="foo", preferred_name="League Manager User"
    )
    models.LeagueUserPermission.objects.create(
        user=user,
        league=enabled_league,
        permission=models.UserPermission.LEAGUE_MANAGER,
    )
    return user


@pytest.fixture
def event_manager_user(enabled_league):
    user = models.User.objects.create(
        password="foo", preferred_name="Event Manager User"
    )
    models.LeagueUserPermission.objects.create(
        user=user, league=enabled_league, permission=models.UserPermission.EVENT_MANAGER
    )
    return user


@pytest.fixture
def full_privilege_user(enabled_league):
    user = models.User.objects.create(
        password="foo", preferred_name="Full Privilege User"
    )
    models.LeagueUserPermission.objects.create(
        user=user, league=enabled_league, permission=models.UserPermission.EVENT_MANAGER
    )
    models.LeagueUserPermission.objects.create(
        user=user,
        league=enabled_league,
        permission=models.UserPermission.LEAGUE_MANAGER,
    )
    return user


@pytest.fixture
def anonymous_user(db):
    return AnonymousUser()


@pytest.fixture
def unprivileged_user(db):
    return models.User.objects.create(
        password="foo", preferred_name="Unprivileged User"
    )


def test_league_query_set__event_manageable(
    enabled_league,
    event_manager_user,
    league_manager_user,
    full_privilege_user,
    unprivileged_user,
):
    assert enabled_league in models.League.objects.event_manageable(event_manager_user)
    assert enabled_league in models.League.objects.event_manageable(full_privilege_user)
    assert enabled_league not in models.League.objects.event_manageable(
        league_manager_user
    )
    assert enabled_league not in models.League.objects.event_manageable(
        unprivileged_user
    )


def test_league_query_set__manageable(
    enabled_league,
    event_manager_user,
    league_manager_user,
    full_privilege_user,
    unprivileged_user,
):
    assert enabled_league not in models.League.objects.manageable(event_manager_user)
    assert enabled_league in models.League.objects.manageable(full_privilege_user)
    assert enabled_league in models.League.objects.manageable(league_manager_user)
    assert enabled_league not in models.League.objects.manageable(unprivileged_user)


def test_league_query_set__visible(
    enabled_league,
    event_manager_user,
    league_manager_user,
    full_privilege_user,
    unprivileged_user,
    anonymous_user,
):
    assert enabled_league in models.League.objects.visible(event_manager_user)
    assert enabled_league in models.League.objects.visible(league_manager_user)
    assert enabled_league in models.League.objects.visible(full_privilege_user)
    assert enabled_league in models.League.objects.visible(unprivileged_user)
    assert enabled_league in models.League.objects.visible(anonymous_user)

    enabled_league.enabled = False
    enabled_league.save()
    disabled_league = enabled_league

    assert disabled_league in models.League.objects.visible(event_manager_user)
    assert disabled_league in models.League.objects.visible(league_manager_user)
    assert disabled_league in models.League.objects.visible(full_privilege_user)
    assert disabled_league not in models.League.objects.visible(unprivileged_user)
    assert disabled_league not in models.League.objects.visible(anonymous_user)
