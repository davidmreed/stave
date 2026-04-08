from zeal import zeal_ignore

from tests.factories import ApplicationFactory

from stave.avail import AvailabilityManager


def test_availability_manager__applications(tournament):
    form = tournament.application_forms.get(slug="apply-nso-so")
    # False-positive N+1 from M2M .add() in test setup.
    with zeal_ignore():
        for role_group in form.role_groups.all():
            role, other_role = role_group.roles.all()[:2]
            ApplicationFactory.create_batch(5, form=form, roles=[role])
            ApplicationFactory.create_batch(5, form=form, roles=[other_role])

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
