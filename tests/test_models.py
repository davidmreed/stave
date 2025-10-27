from stave import models
from stave.management.commands.create_templates import create_templates
import random
from datetime import datetime, date, time
from django.contrib.auth.models import AnonymousUser

import zoneinfo
import pytest
from .factories import (
    ApplicationFactory,
    EventFactory,
    ApplicationFormFactory,
    GameFactory,
)


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
            models.RoleGroupCrewAssignment.objects.create(
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
def league_manager_user(enabled_league, user_factory):
    user = user_factory.create(preferred_name="League Manager User")
    models.LeagueUserPermission.objects.create(
        user=user,
        league=enabled_league,
        permission=models.UserPermission.LEAGUE_MANAGER,
    )
    return user


@pytest.fixture
def event_manager_user(enabled_league, user_factory):
    user = user_factory.create(preferred_name="Event Manager User")
    models.LeagueUserPermission.objects.create(
        user=user, league=enabled_league, permission=models.UserPermission.EVENT_MANAGER
    )
    return user


@pytest.fixture
def full_privilege_user(enabled_league, user_factory):
    user = user_factory.create(preferred_name="Full Privilege User")
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
def anonymous_user():
    return AnonymousUser()


@pytest.fixture
def unprivileged_user(user_factory):
    return user_factory.create(preferred_name="Unprivileged User")


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


def test_event_query_set__visible(
    db, event_manager_user, unprivileged_user, anonymous_user
):
    drafting_event = EventFactory(
        league=event_manager_user.league_permissions.first().league,
        status=models.EventStatus.DRAFTING,
    )
    open_event = EventFactory(
        league=event_manager_user.league_permissions.first().league,
        status=models.EventStatus.OPEN,
    )

    other_event = EventFactory(status=models.EventStatus.DRAFTING)

    assert drafting_event in models.Event.objects.visible(event_manager_user)
    assert drafting_event not in models.Event.objects.visible(unprivileged_user)
    assert drafting_event not in models.Event.objects.visible(anonymous_user)

    assert open_event in models.Event.objects.visible(event_manager_user)
    assert open_event in models.Event.objects.visible(unprivileged_user)
    assert open_event in models.Event.objects.visible(anonymous_user)

    assert other_event not in models.Event.objects.visible(event_manager_user)
    assert other_event not in models.Event.objects.visible(unprivileged_user)
    assert other_event not in models.Event.objects.visible(anonymous_user)


def test_event_query_set__listed(
    db, event_manager_user, unprivileged_user, anonymous_user
):
    link_only_event = EventFactory(
        league=event_manager_user.league_permissions.first().league,
        status=models.EventStatus.LINK_ONLY,
    )
    open_event = EventFactory(
        league=event_manager_user.league_permissions.first().league,
        status=models.EventStatus.OPEN,
    )

    completed_event = EventFactory(status=models.EventStatus.COMPLETE)

    assert link_only_event in models.Event.objects.listed(event_manager_user)
    assert link_only_event not in models.Event.objects.listed(unprivileged_user)
    assert link_only_event not in models.Event.objects.listed(anonymous_user)

    assert open_event in models.Event.objects.listed(event_manager_user)
    assert open_event in models.Event.objects.listed(unprivileged_user)
    assert open_event in models.Event.objects.listed(anonymous_user)

    assert completed_event not in models.Event.objects.listed(event_manager_user)
    assert completed_event not in models.Event.objects.listed(unprivileged_user)
    assert completed_event not in models.Event.objects.listed(anonymous_user)


def test_event_query_set__manageable(db, event_manager_user, unprivileged_user):
    open_event = EventFactory(
        league=event_manager_user.league_permissions.first().league,
        status=models.EventStatus.OPEN,
    )
    other_event = EventFactory()

    assert open_event in models.Event.objects.manageable(event_manager_user)
    assert other_event not in models.Event.objects.manageable(event_manager_user)

    assert not models.Event.objects.manageable(unprivileged_user)


def test_game_query_set__manageable(db, event_manager_user, unprivileged_user):
    open_event = GameFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.OPEN,
    )
    other_event = GameFactory()

    assert open_event in models.Game.objects.manageable(event_manager_user)
    assert other_event not in models.Game.objects.manageable(event_manager_user)

    assert not models.Game.objects.manageable(unprivileged_user)


def test_application_form_query_set__listed(
    db, event_manager_user, unprivileged_user, anonymous_user
):
    form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.OPEN,
    )
    drafting_form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.DRAFTING,
    )
    hidden_form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.OPEN,
        hidden=True,
    )
    closed_form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.OPEN,
        hidden=True,
    )
    other_league_closed_form = ApplicationFormFactory(
        event__status=models.EventStatus.OPEN, hidden=True
    )
    other_league_not_enabled_form = ApplicationFormFactory(
        event__league__enabled=False,
        event__status=models.EventStatus.OPEN,
    )

    assert form in models.ApplicationForm.objects.listed(event_manager_user)
    assert form in models.ApplicationForm.objects.listed(unprivileged_user)
    assert form in models.ApplicationForm.objects.listed(anonymous_user)

    assert drafting_form in models.ApplicationForm.objects.listed(event_manager_user)
    assert drafting_form not in models.ApplicationForm.objects.listed(unprivileged_user)
    assert drafting_form not in models.ApplicationForm.objects.listed(anonymous_user)

    assert hidden_form in models.ApplicationForm.objects.listed(event_manager_user)
    assert hidden_form not in models.ApplicationForm.objects.listed(unprivileged_user)
    assert hidden_form not in models.ApplicationForm.objects.listed(anonymous_user)

    assert closed_form in models.ApplicationForm.objects.listed(event_manager_user)
    assert closed_form not in models.ApplicationForm.objects.listed(unprivileged_user)
    assert closed_form not in models.ApplicationForm.objects.listed(anonymous_user)

    assert other_league_closed_form not in models.ApplicationForm.objects.listed(
        event_manager_user
    )
    assert other_league_closed_form not in models.ApplicationForm.objects.listed(
        unprivileged_user
    )
    assert other_league_closed_form not in models.ApplicationForm.objects.listed(
        anonymous_user
    )

    assert other_league_not_enabled_form not in models.ApplicationForm.objects.listed(
        event_manager_user
    )
    assert other_league_not_enabled_form not in models.ApplicationForm.objects.listed(
        unprivileged_user
    )
    assert other_league_not_enabled_form not in models.ApplicationForm.objects.listed(
        anonymous_user
    )


def test_application_form_query_set__accessible(
    db, event_manager_user, unprivileged_user, anonymous_user
):
    form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.OPEN,
    )
    link_only_form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.LINK_ONLY,
    )
    drafting_form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.DRAFTING,
    )
    other_league_not_enabled_form = ApplicationFormFactory(
        event__league__enabled=False,
        event__status=models.EventStatus.OPEN,
    )

    assert form in models.ApplicationForm.objects.accessible(event_manager_user)
    assert form in models.ApplicationForm.objects.accessible(unprivileged_user)
    assert form in models.ApplicationForm.objects.accessible(anonymous_user)

    assert link_only_form in models.ApplicationForm.objects.accessible(
        event_manager_user
    )
    assert link_only_form in models.ApplicationForm.objects.accessible(
        unprivileged_user
    )
    assert link_only_form in models.ApplicationForm.objects.accessible(anonymous_user)

    assert drafting_form in models.ApplicationForm.objects.accessible(
        event_manager_user
    )
    assert drafting_form not in models.ApplicationForm.objects.accessible(
        unprivileged_user
    )
    assert drafting_form not in models.ApplicationForm.objects.accessible(
        anonymous_user
    )

    assert (
        other_league_not_enabled_form
        not in models.ApplicationForm.objects.accessible(event_manager_user)
    )
    assert (
        other_league_not_enabled_form
        not in models.ApplicationForm.objects.accessible(unprivileged_user)
    )
    assert (
        other_league_not_enabled_form
        not in models.ApplicationForm.objects.accessible(anonymous_user)
    )


def test_application_form_query_set__submittable(
    db, event_manager_user, unprivileged_user, anonymous_user
):
    form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.OPEN,
    )
    complete_event_form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.COMPLETE,
    )
    closed_form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        closed=True,
    )
    closed_other_league_form = ApplicationFormFactory(
        closed=True,
    )

    assert form in models.ApplicationForm.objects.submittable(event_manager_user)
    assert form in models.ApplicationForm.objects.submittable(unprivileged_user)
    assert form in models.ApplicationForm.objects.submittable(anonymous_user)

    assert complete_event_form not in models.ApplicationForm.objects.submittable(
        event_manager_user
    )
    assert complete_event_form not in models.ApplicationForm.objects.submittable(
        unprivileged_user
    )
    assert complete_event_form not in models.ApplicationForm.objects.submittable(
        anonymous_user
    )

    assert closed_form in models.ApplicationForm.objects.submittable(event_manager_user)
    assert closed_form not in models.ApplicationForm.objects.submittable(
        unprivileged_user
    )
    assert closed_form not in models.ApplicationForm.objects.submittable(anonymous_user)

    assert closed_other_league_form not in models.ApplicationForm.objects.submittable(
        event_manager_user
    )
    assert closed_other_league_form not in models.ApplicationForm.objects.submittable(
        unprivileged_user
    )
    assert closed_other_league_form not in models.ApplicationForm.objects.submittable(
        anonymous_user
    )


def test_application_form_query_set__manageable(
    db, event_manager_user, unprivileged_user, anonymous_user
):
    form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.OPEN,
    )
    complete_event_form = ApplicationFormFactory(
        event__league=event_manager_user.league_permissions.first().league,
        event__status=models.EventStatus.COMPLETE,
    )

    assert form in models.ApplicationForm.objects.manageable(event_manager_user)
    assert form not in models.ApplicationForm.objects.manageable(unprivileged_user)

    assert complete_event_form not in models.ApplicationForm.objects.manageable(
        event_manager_user
    )
    assert complete_event_form not in models.ApplicationForm.objects.manageable(
        unprivileged_user
    )

    assert not models.ApplicationForm.objects.manageable(anonymous_user)


def test_application_query_set__visible__self(db, unprivileged_user):
    """Applications should be visible to their submitters"""
    application = ApplicationFactory(user=unprivileged_user)
    assert application in models.Application.objects.visible(unprivileged_user)


def test_application_query_set__visible__event_manager(db, event_manager_user):
    """Applications should be visible to event manager users from the same league"""
    application = ApplicationFactory(
        form__event__league=event_manager_user.league_permissions.first().league
    )
    other_league_application = ApplicationFactory()
    assert application in models.Application.objects.visible(event_manager_user)
    assert other_league_application not in models.Application.objects.visible(
        event_manager_user
    )


def test_application_query_set__visible__other(db, unprivileged_user):
    """Applications should not be visible to unrelated, unprivileged users"""
    application = ApplicationFactory()
    assert application not in models.Application.objects.visible(unprivileged_user)


def test_application_query_set__open(db):
    application = ApplicationFactory(status=models.ApplicationStatus.APPLIED)
    closed_application = ApplicationFactory(status=models.ApplicationStatus.WITHDRAWN)

    assert application in models.Application.objects.open()
    assert closed_application not in models.Application.objects.open()


def test_application_query_set__in_progress(db):
    application = ApplicationFactory(status=models.ApplicationStatus.INVITATION_PENDING)
    closed_application = ApplicationFactory(status=models.ApplicationStatus.WITHDRAWN)

    assert application in models.Application.objects.in_progress()
    assert closed_application not in models.Application.objects.in_progress()


def test_application_query_set__staffed(db):
    application = ApplicationFactory(status=models.ApplicationStatus.ASSIGNED)
    closed_application = ApplicationFactory(status=models.ApplicationStatus.WITHDRAWN)

    assert application in models.Application.objects.staffed()
    assert closed_application not in models.Application.objects.staffed()


def test_application_query_set__closed(db):
    application = ApplicationFactory(status=models.ApplicationStatus.ASSIGNED)
    closed_application = ApplicationFactory(status=models.ApplicationStatus.WITHDRAWN)

    assert application not in models.Application.objects.closed()
    assert closed_application in models.Application.objects.closed()


def test_application_query_set__pending(db):
    application = ApplicationFactory(status=models.ApplicationStatus.ASSIGNMENT_PENDING)
    closed_application = ApplicationFactory(status=models.ApplicationStatus.WITHDRAWN)

    assert application in models.Application.objects.pending()
    assert closed_application not in models.Application.objects.pending()
