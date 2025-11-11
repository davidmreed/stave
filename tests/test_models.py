from stave import models

from .factories import (
    ApplicationFactory,
    EventFactory,
    ApplicationFormFactory,
    GameFactory,
    RoleGroupFactory,
    LeagueTemplateFactory,
    EventTemplateFactory,
    ApplicationFormTemplateFactory,
    ApplicationFormTemplateAssignmentFactory,
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

    assert closed_form not in models.ApplicationForm.objects.submittable(
        event_manager_user
    )
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


def test_clone_templates(db):
    league_template = LeagueTemplateFactory()
    event_template = EventTemplateFactory(two_day=True, league_template=league_template)
    role_group_template = RoleGroupFactory(
        with_league_template=True, league_template=league_template
    )
    application_form_template = ApplicationFormTemplateFactory(
        with_league_template=True, league_template=league_template
    )
    ApplicationFormTemplateAssignmentFactory(
        application_form_template=application_form_template,
        event_template=event_template,
    )

    league = league_template.clone()

    assert league.role_groups.count() == 1
    assert league.role_groups.first().roles.count() == role_group_template.roles.count()
    assert league.event_templates.count() == 1
    assert league.application_form_templates.count() == 1
    assert (
        models.ApplicationFormTemplateAssignment.objects.filter(
            application_form_template__league=league
        ).count()
        == 1
    )
    assert (
        league.message_templates.count() == 3
    )  # one per type for a single ApplicationFormTemplate
