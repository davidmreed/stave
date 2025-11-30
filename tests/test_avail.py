from tests.factories import ApplicationFactory, CrewFactory
from datetime import datetime, timedelta, timezone
from stave.avail import AvailabilityManager, UserAvailabilityEntry, ConflictKind
from pytest import fixture
from stave import models

@fixture
def existing_entry(db):
    start_time = datetime.now(tz=timezone.utc)
    end_time = start_time + timedelta(hours=2)
    return UserAvailabilityEntry(
        crew = CrewFactory(kind=models.CrewKind.OVERRIDE_CREW),
        start_time=start_time,
        end_time=end_time,
        exclusive=True
    )
@fixture
def existing_static_crew_entry(db):
    start_time = datetime.now(tz=timezone.utc)
    end_time = start_time + timedelta(hours=2)
    return UserAvailabilityEntry(
        crew = CrewFactory(kind=models.CrewKind.GAME_CREW),
        start_time=start_time,
        end_time=end_time,
        exclusive=True
    )

def test_user_availability_entry__simple_overlap(existing_entry):
    assert existing_entry.overlaps(UserAvailabilityEntry(
        crew=existing_entry.crew,
        start_time=existing_entry.start_time,
        end_time=existing_entry.end_time,
        exclusive=True
    ), set()) == ConflictKind.SWAPPABLE_CONFLICT
def test_user_availability_entry__simple_overlap_nonexclusive(existing_entry):
    assert existing_entry.overlaps(UserAvailabilityEntry(
        crew=existing_entry.crew,
        start_time=existing_entry.start_time,
        end_time=existing_entry.end_time,
        exclusive=False
    ), set()) == ConflictKind.NONE

def test_user_availability_entry__simple_overlap_other_role_group(existing_entry):
    assert existing_entry.overlaps(UserAvailabilityEntry(
        crew=CrewFactory(kind=models.CrewKind.OVERRIDE_CREW),
        start_time=existing_entry.start_time,
        end_time=existing_entry.end_time,
        exclusive=True
    ), set()) == ConflictKind.NON_SWAPPABLE_CONFLICT

def test_user_availability_entry__swappable_overlap_other_role_group(existing_entry):
    other_crew = CrewFactory(kind=models.CrewKind.OVERRIDE_CREW)
    assert existing_entry.overlaps(UserAvailabilityEntry(
        crew=other_crew,
        start_time=existing_entry.start_time,
        end_time=existing_entry.end_time,
        exclusive=False
    ),set([other_crew.role_group])) == ConflictKind.SWAPPABLE_CONFLICT

def test_user_availability_entry__partial_overlap(existing_entry):
    assert existing_entry.overlaps(UserAvailabilityEntry(
        crew=existing_entry.crew,
        start_time=existing_entry.start_time + timedelta(hours=1),
        end_time=existing_entry.end_time,
        exclusive=True
    ), set()) == ConflictKind.SWAPPABLE_CONFLICT

def test_user_availability_entry__event_crews():
    ...

def test_user_availability_entry__static_crews(existing_static_crew_entry):
    assert existing_static_crew_entry.overlaps(UserAvailabilityEntry(
        crew=existing_static_crew_entry.crew,
        start_time=None,
        end_time=None,
        exclusive=True
    ), set()) == ConflictKind.SWAPPABLE_CONFLICT

def test_user_availability_entry__static_crews_nonexclusive(existing_static_crew_entry):
    assert existing_static_crew_entry.overlaps(UserAvailabilityEntry(
        crew=existing_static_crew_entry.crew,
        start_time=None,
        end_time=None,
        exclusive=False
    ), set()) == ConflictKind.NONE

def test_user_availability_entry__static_crews_other_role_group(existing_static_crew_entry):
    assert existing_static_crew_entry.overlaps(UserAvailabilityEntry(
        crew=CrewFactory(kind=models.CrewKind.GAME_CREW),
        start_time=None,
        end_time=None,
        exclusive=True
    ), set()) == ConflictKind.NON_SWAPPABLE_CONFLICT

def test_user_availability_entry__static_crews_swappable_role_group(existing_static_crew_entry):
    other_crew = CrewFactory(kind=models.CrewKind.GAME_CREW)
    assert existing_static_crew_entry.overlaps(UserAvailabilityEntry(
        crew=CrewFactory(kind=models.CrewKind.GAME_CREW),
        start_time=None,
        end_time=None,
        exclusive=True
    ), set([other_crew.role_group])) == ConflictKind.SWAPPABLE_CONFLICT

def test_user_availability_entry__override_of_static_crew():
    ...

def test_user_availability_entry__non_meaningful():
    ...

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
