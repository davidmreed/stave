from tests.factories import ApplicationFactory

from stave.avail import AvailabilityManager


def test_availability_manager__applications(tournament):
    form = tournament.application_forms.get(slug="apply-nso-so")
    for role_group in form.role_groups.all():
        role, other_role = role_group.roles.all()[:2]
        applications = [ApplicationFactory(form=form) for i in range(5)]
        for application in applications:
            application.roles.set([role])
        applications = [ApplicationFactory(form=form) for i in range(5)]
        for application in applications:
            application.roles.set([other_role])

    am = AvailabilityManager.with_application_form(form)
    assert set(am.applications.keys()) == {
        role_group.id for role_group in form.role_groups.all()
    }
    for key in am.applications:
        roles = form.role_groups.get(id=key).roles.all()
        assert set(am.applications[key].keys()) == {role.name for role in roles[:2]}
        for role in roles[:2]:
            assert len(am.applications[key][role.name]) == 5

    # TODO: test exclusion by application status
    # TODO: test that prefetches cache


def test_availability_manager__static_crews(): ...


def test_availability_manager__event_crews(): ...


def test_availability_manager__user_availability(): ...


def test_availability_manager__user_event_availability(): ...


def test_availability_manager__user_static_crew_availability(): ...


def test_availability_manager__get_application_counts(): ...


def test_availability_manager__get_all_applications(): ...


def test_availability_manager__get_available_applications(): ...
