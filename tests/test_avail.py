from tests.factories import ApplicationFactory, CrewFactory, ApplicationFormFactory, UserFactory
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


def test_user_availability_entry__abutting_left_same_crew_exclusive(existing_entry):
    assert (
        existing_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_entry.crew,
                start_time=existing_entry.end_time,
                end_time=existing_entry.end_time + timedelta(hours=2),
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.NONE
    )


def test_user_availability_entry__abutting_right_same_crew_exclusive(existing_entry):
    assert (
        existing_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_entry.crew,
                start_time=existing_entry.start_time - timedelta(hours=2),
                end_time=existing_entry.start_time,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.NONE
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


def test_user_availability_entry__overlap_same_static_crew_exclusive(
    existing_static_crew_entry,
):
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


def test_user_availability_entry__overlap_same_static_crew_nonexclusive(
    existing_static_crew_entry,
):
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


def test_user_availability_entry__overlap_same_event_crew_exclusive(
    existing_event_crew_entry,
):
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


def test_user_availability_entry__overlap_same_event_crew_nonexclusive(
    existing_event_crew_entry,
):
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


def test_user_availability_entry__overlap_other_event_crew_non_swappable(
    existing_event_crew_entry,
):
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


def test_user_availability_entry__overlap_other_event_crew_swappable(
    existing_event_crew_entry,
):
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
    #


def test_availability_manager__applications_by_status(db):
    application_form = ApplicationFormFactory()
    for status in models.ApplicationStatus:
        for _ in range(3):
            ApplicationFactory(form=application_form, status=status)

    am = AvailabilityManager.with_application_form(application_form)
    by_status = am.applications_by_status

    # AvailabilityManager doesn't pull apps in statuses
    # that have no effect on availability, like Withdrawn
    assert set(by_status.keys()).issubset(set(v.value for v in models.ApplicationStatus))
    assert all(len(v) == 3 for v in by_status.values())


def test_availability_manager__get_applications_in_statuses(db):
    application_form = ApplicationFormFactory()
    for status in models.ApplicationStatus:
        for i in range(3):
            ApplicationFactory(
                user__preferred_name="CBA"[i], form=application_form, status=status
            )

    am = AvailabilityManager.with_application_form(application_form)
    in_statuses = am.get_applications_in_statuses(
        (models.ApplicationStatus.APPLIED, models.ApplicationStatus.ASSIGNED)
    )

    assert len(in_statuses) == 6
    assert in_statuses == sorted(in_statuses, key=lambda a: a.user.preferred_name)


def test_availability_manager__static_crews(db):
    application_form = ApplicationFormFactory()
    application_form.role_groups.set(application_form.event.league.role_groups.all())

    # The AvailabilityManager requires crews to share one of
    # the AppForm's Role Groups.
    crew = CrewFactory(event=application_form.event, role_group=application_form.role_groups.first(), kind=models.CrewKind.GAME_CREW)
    CrewFactory(event=application_form.event, role_group=application_form.role_groups.first(), kind=models.CrewKind.EVENT_CREW)
    CrewFactory(kind=models.CrewKind.GAME_CREW)
    am = AvailabilityManager.with_application_form(application_form)

    assert am.static_crews == [crew]


def test_availability_manager__event_crews(db):
    application_form = ApplicationFormFactory()
    application_form.role_groups.set(application_form.event.league.role_groups.all())
    crew = CrewFactory(event=application_form.event, role_group=application_form.role_groups.first(), kind=models.CrewKind.EVENT_CREW)
    CrewFactory(event=application_form.event, role_group=application_form.role_groups.first(), kind=models.CrewKind.GAME_CREW)
    CrewFactory(kind=models.CrewKind.EVENT_CREW)
    am = AvailabilityManager.with_application_form(application_form)

    assert am.event_crews == [crew]




def test_applications_by_role_group():...

def test_role_groups():...

def test_game_crew_assignments():...

def test_user_availability():...

def test_user_event_availability():...
def test_user_static_crew_availability():...
def test_get_game_count_for_user(): ...

def test_game_counts_by_user(): ...

def test_get_application_counts(): ...
def test_get_all_applications(): ...

def test_get_application_entries(): ...

def test_get_swappable_assignments(): ...

def test_get_application_by_id(): ...

def test_get_application_for_user():...

def test_get_application_for_assignment(): ...

def test_get_assignment(): ...

def test_set_assignment__open_slot(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.APPLIED,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY
    )
    role = application.roles.first()
    crew = CrewFactory(
        event=application.form.event,
        role_group=role.role_group
    )

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, application.user)

    assert crew.get_assignments_by_role_id()[role.id].user == application.user
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.ASSIGNMENT_PENDING

def test_set_assignment__replace_existing(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY
    )
    role = application.roles.first()
    other_application = ApplicationFactory(
        form=application.form,
        status=models.ApplicationStatus.APPLIED
    )
    other_application.roles.set([role])
    crew = CrewFactory(
        event=application.form.event,
        role_group=role.role_group
    )
    models.CrewAssignment.objects.create(
        user=application.user,
        crew=crew,
        role=role
    )

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    assert not models.CrewAssignment.objects.filter(
        user=application.user
    ).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING

def test_set_assignment__remove_existing(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY
    )
    role = application.roles.first()
    crew = CrewFactory(
        event=application.form.event,
        role_group=role.role_group
    )
    models.CrewAssignment.objects.create(
        user=application.user,
        crew=crew,
        role=role
    )

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, None)

    assert role.id not in crew.get_assignments_by_role_id()
    assert not models.CrewAssignment.objects.filter(
        user=application.user
    ).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED

def test_set_assignment__swap_roles_override_crew(db):...


def test_set_assignment__swap_roles_static_crew_to_override_crew(db): ...
def test_set_assignment__swap_roles_static_crew_to_blank(db): ...
def test_set_assignment__swap_roles_event_crew(db): ...

def test_set_assignment__swap_roles_static_crew_to_override_crew_keep_nonexclusive(db): ...
def test_set_assignment__swap_roles_event_crew_keep_nonexclusive(db): ...
def test_set_assignment__static_crew_override_replace_blank_with_original(db): ...

def test_set_crew_assignment(): ...
