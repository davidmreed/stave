from pytest_factoryboy import register

from datetime import datetime, date, time
from django.contrib.auth.models import AnonymousUser

import zoneinfo
import pytest

from stave import models
from tests import factories

# See: https://pytest-factoryboy.readthedocs.io/
register(factories.EventFactory)
register(factories.LeagueFactory)
register(factories.UserFactory)
register(factories.ApplicationFormFactory)
register(factories.ApplicationResponseFactory)
register(factories.CrewFactory)
register(factories.QuestionFactory)
register(factories.RoleGroupFactory)
register(factories.RoleFactory)
register(factories.LeagueUserPermissionFactory)
register(factories.GameFactory)
register(factories.RoleGroupCrewAssignmentFactory)


@pytest.fixture
def enabled_league(db, league_factory):
    return league_factory(enabled=True)


@pytest.fixture
def timezone(enabled_league):
    return zoneinfo.ZoneInfo(enabled_league.time_zone)


@pytest.fixture
def role_group_nso(enabled_league, role_group_factory):
    return role_group_factory(name="NSO", league=enabled_league)


@pytest.fixture
def role_group_so(enabled_league, role_group_factory):
    return role_group_factory(name="SO", league=enabled_league)


@pytest.fixture
def role_group_tho(enabled_league, role_group_factory):
    return role_group_factory(name="THO", league=enabled_league, event_only=True)


@pytest.fixture
def tournament(
    enabled_league,
    timezone,
    role_group_so,
    role_group_nso,
    role_group_tho,
    event_factory,
    game_factory,
    application_form_factory,
    role_group_crew_assignment_factory,
    question_factory,
):
    tournament = event_factory(
        league=enabled_league,
        name="Outer Planets Throwdown",
        status=models.EventStatus.OPEN,
        slug="outer-planets-throwdown",
        start_date=date(2218, 5, 25),
        end_date=date(2218, 5, 26),
        location="Ceres Station Level 6",
    )
    games = [
        game_factory(
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
        ),
        game_factory(
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
        ),
        game_factory(
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
        ),
        game_factory(
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
        ),
        game_factory(
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
        ),
    ]

    for game in games:
        for role_group in [role_group_so, role_group_nso]:
            role_group_crew_assignment_factory(game=game, role_group=role_group)

    ## Create application forms for the tournament
    app_form = application_form_factory(
        event=tournament,
        slug="apply-nso-so",
        application_kind=models.ApplicationKind.CONFIRM_THEN_ASSIGN,
        application_availability_kind=models.ApplicationAvailabilityKind.BY_DAY,
        intro_text="Join the best teams in the Belt! **For beltalowda!**",
        requires_profile_fields=["preferred_name"],
    )
    app_form.role_groups.set([role_group_nso, role_group_so])

    question_factory(
        application_form=app_form,
        content="What is your affiliated faction?",
        kind=models.QuestionKind.SELECT_ONE,
        options=["Golden Bough", "OPA", "Free Navy"],
        required=True,
        order_key=1,
    )
    question_factory(
        application_form=app_form,
        content="What kinds of kibble do you like?",
        kind=models.QuestionKind.SELECT_MANY,
        options=["red", "blue", "green"],
        allow_other=True,
        required=True,
        order_key=2,
    )
    question_factory(
        application_form=app_form,
        content="What are your special skills?",
        kind=models.QuestionKind.LONG_TEXT,
        order_key=3,
    )
    question_factory(
        application_form=app_form,
        content="What do you think of Marco Inaros?",
        kind=models.QuestionKind.SHORT_TEXT,
        order_key=4,
    )

    app_form_tho = application_form_factory(
        event=tournament,
        slug="apply-tho",
        application_kind=models.ApplicationKind.ASSIGN_ONLY,
        application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT,
        intro_text="Join the best teams in the Belt as a tournament leader. **For beltalowda!**",
        requires_profile_fields=["preferred_name"],
    )
    app_form_tho.role_groups.set([role_group_tho])

    question_factory(
        application_form=app_form_tho,
        content="What do you want to do?",
        kind=models.QuestionKind.LONG_TEXT,
        required=True,
        order_key=1,
    )

    return tournament


@pytest.fixture
def league_manager_user(enabled_league, league_user_permission_factory):
    permission = league_user_permission_factory(
        user__preferred_name="League Manager User",
        league=enabled_league,
        permission=models.UserPermission.LEAGUE_MANAGER,
    )
    return permission.user


@pytest.fixture
def event_manager_user(enabled_league, league_user_permission_factory):
    permission = league_user_permission_factory(
        user__preferred_name="Event Manager User",
        league=enabled_league,
        permission=models.UserPermission.EVENT_MANAGER,
    )
    return permission.user


@pytest.fixture
def full_privilege_user(enabled_league, league_user_permission_factory):
    event_perm = league_user_permission_factory(
        user__preferred_name="Full Privilege User",
        league=enabled_league,
        permission=models.UserPermission.EVENT_MANAGER,
    )
    league_user_permission_factory(
        user=event_perm.user,
        league=enabled_league,
        permission=models.UserPermission.LEAGUE_MANAGER,
    )
    return event_perm.user


@pytest.fixture
def anonymous_user():
    return AnonymousUser()


@pytest.fixture
def unprivileged_user(user_factory):
    return user_factory.create(preferred_name="Unprivileged User")
