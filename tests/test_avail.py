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
    assert set(am.applications_by_role_group.keys()) == {
        role_group.id for role_group in form.role_groups.all()
    }
    for key in am.applications_by_role_group:
        roles = form.role_groups.get(id=key).roles.all()
        assert set(am.applications_by_role_group[key].keys()) == {
            role.name for role in roles[:2]
        }
        for role in roles[:2]:
            assert len(am.applications_by_role_group[key][role.name]) == 5

    # TODO: test exclusion by application status
    # TODO: test that prefetches cache
