from zeal import zeal_ignore

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
        crew=CrewFactory(kind=models.CrewKind.OVERRIDE_CREW),
        start_time=start_time,
        end_time=end_time,
        exclusive=True,
    )


@fixture
def existing_static_crew_entry(db):
    return UserAvailabilityEntry(
        crew=CrewFactory(kind=models.CrewKind.GAME_CREW),
        start_time=None,
        end_time=None,
        exclusive=True,
    )

@fixture
def existing_event_crew_entry(db):
    return UserAvailabilityEntry(
        crew=CrewFactory(kind=models.CrewKind.EVENT_CREW),
        start_time=None,
        end_time=None,
        exclusive=True,
    )


def test_user_availability_entry__full_overlap_same_crew_exclusive(existing_entry):
    assert (
        existing_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_entry.crew,
                start_time=existing_entry.start_time,
                end_time=existing_entry.end_time,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.SWAPPABLE_CONFLICT
    )


def test_user_availability_entry__full_overlap_same_crew_nonexclusive(existing_entry):
    assert (
        existing_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_entry.crew,
                start_time=existing_entry.start_time,
                end_time=existing_entry.end_time,
                exclusive=False,
            ),
            set(),
        )
        == ConflictKind.NONE
    )


def test_user_availability_entry__full_overlap_other_crew_non_swappable(existing_entry):
    assert (
        existing_entry.overlaps(
            UserAvailabilityEntry(
                crew=CrewFactory(kind=models.CrewKind.OVERRIDE_CREW),
                start_time=existing_entry.start_time,
                end_time=existing_entry.end_time,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.NON_SWAPPABLE_CONFLICT
    )


def test_user_availability_entry__full_overlap_other_crew_swappable(existing_entry):
    other_crew = CrewFactory(kind=models.CrewKind.OVERRIDE_CREW)
    assert (
        existing_entry.overlaps(
            UserAvailabilityEntry(
                crew=other_crew,
                start_time=existing_entry.start_time,
                end_time=existing_entry.end_time,
                exclusive=False,
            ),
            set([other_crew.role_group]),
        )
        == ConflictKind.SWAPPABLE_CONFLICT
    )


def test_user_availability_entry__partial_overlap(existing_entry):
    assert (
        existing_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_entry.crew,
                start_time=existing_entry.start_time + timedelta(hours=1),
                end_time=existing_entry.end_time,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.SWAPPABLE_CONFLICT
    )


def test_user_availability_entry__overlap_same_static_crew_exclusive(existing_static_crew_entry):
    assert (
        existing_static_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_static_crew_entry.crew,
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.SWAPPABLE_CONFLICT
    )


def test_user_availability_entry__overlap_same_static_crew_nonexclusive(existing_static_crew_entry):
    assert (
        existing_static_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_static_crew_entry.crew,
                start_time=None,
                end_time=None,
                exclusive=False,
            ),
            set(),
        )
        == ConflictKind.NONE
    )


def test_user_availability_entry__overlap_other_static_crew_non_swappable(
    existing_static_crew_entry,
):
    assert (
        existing_static_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=CrewFactory(kind=models.CrewKind.GAME_CREW),
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.NON_SWAPPABLE_CONFLICT
    )


def test_user_availability_entry__overlap_other_static_crew_swappable(
    existing_static_crew_entry,
):
    other_crew = CrewFactory(kind=models.CrewKind.GAME_CREW)
    assert (
        existing_static_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=other_crew,
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set([other_crew.role_group]),
        )
        == ConflictKind.SWAPPABLE_CONFLICT
    )


def test_user_availability_entry__override_of_static_crew(): ...

def test_user_availability_entry__overlap_same_event_crew_exclusive(existing_event_crew_entry):
    assert (
        existing_event_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_event_crew_entry.crew,
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.SWAPPABLE_CONFLICT
    )

def test_user_availability_entry__overlap_same_event_crew_nonexclusive(existing_event_crew_entry):
    assert (
        existing_event_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_event_crew_entry.crew,
                start_time=None,
                end_time=None,
                exclusive=False,
            ),
            set(),
        )
        == ConflictKind.NONE
    )

def test_user_availability_entry__overlap_other_event_crew_non_swappable(existing_event_crew_entry):
    assert (
        existing_event_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=CrewFactory(kind=models.CrewKind.EVENT_CREW),
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.NON_SWAPPABLE_CONFLICT
    )

def test_user_availability_entry__overlap_other_event_crew_swappable(existing_event_crew_entry):
    other_crew = CrewFactory(kind=models.CrewKind.EVENT_CREW)
    assert (
        existing_event_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=other_crew,
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set([other_crew.role_group]),
        )
        == ConflictKind.SWAPPABLE_CONFLICT
    )

def test_user_availability_entry__non_meaningful(existing_event_crew_entry):
    other_crew = CrewFactory(kind=models.CrewKind.GAME_CREW)
    assert (
        existing_event_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=other_crew,
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.NONE
    )
