from tests.factories import (
    ApplicationFactory,
    CrewFactory,
    ApplicationFormFactory,
    RoleFactory,
    GameFactory,
    UserFactory,
)
from datetime import datetime, timedelta, timezone
from stave.avail import AvailabilityManager, UserAvailabilityEntry, ConflictKind
from pytest import fixture
from stave import models


@fixture
def existing_entry(db):
    start_time = datetime.now(tz=timezone.utc)
    end_time = start_time + timedelta(hours=2)
    crew = CrewFactory(kind=models.CrewKind.OVERRIDE_CREW)
    role = crew.role_group.roles.first()

    return UserAvailabilityEntry(
        crew=crew,
        role=role,
        start_time=start_time,
        end_time=end_time,
        exclusive=True,
    )


@fixture
def existing_static_crew_entry(db):
    crew = CrewFactory(kind=models.CrewKind.GAME_CREW)
    role = crew.role_group.roles.first()

    return UserAvailabilityEntry(
        crew=crew,
        role=role,
        start_time=None,
        end_time=None,
        exclusive=True,
    )


@fixture
def existing_event_crew_entry(db):
    crew = CrewFactory(kind=models.CrewKind.EVENT_CREW)
    role = crew.role_group.roles.first()

    return UserAvailabilityEntry(
        crew=crew,
        role=role,
        start_time=None,
        end_time=None,
        exclusive=True,
    )


def test_user_availability_entry__full_overlap_same_crew_exclusive(existing_entry):
    assert (
        existing_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_entry.crew,
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set([other_crew.role_group]),
        )
        == ConflictKind.SWAPPABLE_CONFLICT
    )


def test_user_availability_entry__override_of_static_crew(db):
    # DMR: this is testing the wrong thing.
    # Test overlap between override crew and static crew assigned to same game
    # (same times, same role_group) - this is a self-swap case

    # Create a static crew
    static_crew = CrewFactory(kind=models.CrewKind.GAME_CREW)
    role = static_crew.role_group.roles.first()

    # Create an override crew for the same role_group
    override_crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=static_crew.event,
        role_group=static_crew.role_group,
    )
    game = GameFactory(event=static_crew.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew=static_crew,
        crew_overrides=override_crew,
        game=game,
        role_group=static_crew.role_group,
    )

    # Both entries have same times (from the game) and same role_group
    override_entry = UserAvailabilityEntry(
        crew=override_crew,
        role=role,
        start_time=game.start_time,
        end_time=game.end_time,
        exclusive=True,
    )
    static_entry = UserAvailabilityEntry(
        crew=static_crew,
        role=role,
        start_time=game.start_time,
        end_time=game.end_time,
        exclusive=True,
    )

    # Same times and same role_group -> self-swap case
    # Both exclusive -> SWAPPABLE_CONFLICT
    assert (
        override_entry.overlaps(static_entry, set()) == ConflictKind.SWAPPABLE_CONFLICT
    )
    assert (
        static_entry.overlaps(override_entry, set()) == ConflictKind.SWAPPABLE_CONFLICT
    )

    # If one is nonexclusive -> NONE
    static_entry_nonexclusive = UserAvailabilityEntry(
        crew=static_crew,
        role=role,
        start_time=game.start_time,
        end_time=game.end_time,
        exclusive=False,
    )
    assert (
        override_entry.overlaps(static_entry_nonexclusive, set()) == ConflictKind.NONE
    )
    assert (
        static_entry_nonexclusive.overlaps(override_entry, set()) == ConflictKind.NONE
    )


def test_user_availability_entry__overlap_same_event_crew_exclusive(
    existing_event_crew_entry,
):
    assert (
        existing_event_crew_entry.overlaps(
            UserAvailabilityEntry(
                crew=existing_event_crew_entry.crew,
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
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
                role=models.Role(),
                start_time=None,
                end_time=None,
                exclusive=True,
            ),
            set(),
        )
        == ConflictKind.NONE
    )


def test_availability_manager__applications_by_status(db):
    application_form = ApplicationFormFactory()
    for status in models.ApplicationStatus:
        for _ in range(3):
            ApplicationFactory(form=application_form, status=status)

    am = AvailabilityManager.with_application_form(application_form)
    by_status = am.applications_by_status

    assert list(by_status.keys()) == list(models.ApplicationStatus)
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
    crew = CrewFactory(
        event=application_form.event,
        role_group=application_form.role_groups.first(),
        kind=models.CrewKind.GAME_CREW,
    )
    CrewFactory(
        event=application_form.event,
        role_group=application_form.role_groups.first(),
        kind=models.CrewKind.EVENT_CREW,
    )
    CrewFactory(kind=models.CrewKind.GAME_CREW)
    am = AvailabilityManager.with_application_form(application_form)

    assert am.static_crews == [crew]


def test_availability_manager__event_crews(db):
    application_form = ApplicationFormFactory()
    application_form.role_groups.set(application_form.event.league.role_groups.all())
    crew = CrewFactory(
        event=application_form.event,
        role_group=application_form.role_groups.first(),
        kind=models.CrewKind.EVENT_CREW,
    )
    CrewFactory(
        event=application_form.event,
        role_group=application_form.role_groups.first(),
        kind=models.CrewKind.GAME_CREW,
    )
    CrewFactory(kind=models.CrewKind.EVENT_CREW)
    am = AvailabilityManager.with_application_form(application_form)

    assert am.event_crews == [crew]


def test_role_groups(db):
    application_form = ApplicationFormFactory()

    am = AvailabilityManager.with_application_form(application_form)

    assert am.role_groups == set(application_form.role_groups.all())


def test_game_crew_assignments(db):
    application_form = ApplicationFormFactory()
    role_group = application_form.role_groups.first()
    assert role_group

    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    game = GameFactory(event=application_form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role_group
    )

    user = UserFactory()
    role = role_group.roles.first()
    ca = models.CrewAssignment.objects.create(user=user, crew=crew, role=role)

    am = AvailabilityManager.with_application_form(application_form)

    assignments = list(am.game_crew_assignments)
    assert len(assignments) == 1
    assert assignments[0] == (game, ca)
    # Verify the assignment comes from the override crew
    assert assignments[0][1].crew == crew


def test_user_availability(db):
    application_form = ApplicationFormFactory()
    role_group = application_form.role_groups.first()
    assert role_group

    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    game = GameFactory(event=application_form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role_group
    )

    user = UserFactory()
    role = role_group.roles.first()
    models.CrewAssignment.objects.create(user=user, crew=crew, role=role)

    am = AvailabilityManager.with_application_form(application_form)

    availability = am.user_availability
    assert user.id in availability
    entries = availability[user.id]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.crew == crew
    assert entry.role == role
    assert entry.start_time == game.start_time
    assert entry.end_time == game.end_time
    assert entry.exclusive is True


def test_user_event_availability(db):
    application_form = ApplicationFormFactory()
    role_group = application_form.role_groups.first()
    assert role_group

    crew = CrewFactory(
        kind=models.CrewKind.EVENT_CREW,
        event=application_form.event,
        role_group=role_group,
    )

    user = UserFactory()
    role = role_group.roles.first()
    models.CrewAssignment.objects.create(user=user, crew=crew, role=role)

    am = AvailabilityManager.with_application_form(application_form)

    availability = am.user_event_availability
    assert user.id in availability
    entries = availability[user.id]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.crew == crew
    assert entry.role == role
    assert entry.start_time is None
    assert entry.end_time is None
    assert entry.exclusive is True


def test_user_static_crew_availability(db):
    application_form = ApplicationFormFactory()
    application_form.role_groups.set(application_form.event.league.role_groups.all())
    role_group = application_form.role_groups.first()
    assert role_group

    crew = CrewFactory(
        kind=models.CrewKind.GAME_CREW,
        event=application_form.event,
        role_group=role_group,
    )

    user = UserFactory()
    role = role_group.roles.first()
    models.CrewAssignment.objects.create(user=user, crew=crew, role=role)

    am = AvailabilityManager.with_application_form(application_form)

    availability = am.user_static_crew_availability
    assert user.id in availability
    entries = availability[user.id]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.crew == crew
    assert entry.role == role
    assert entry.start_time is None
    assert entry.end_time is None
    assert entry.exclusive is True


def test_get_game_count_for_user(db):
    application_form = ApplicationFormFactory()
    role_group = application_form.role_groups.first()
    assert role_group

    crew1 = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    crew2 = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    game1 = GameFactory(event=application_form.event, order_key=1)
    game2 = GameFactory(event=application_form.event, order_key=2)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew1, game=game1, role_group=role_group
    )
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew2, game=game2, role_group=role_group
    )

    user = UserFactory()
    user2 = UserFactory()
    role = role_group.roles.first()
    models.CrewAssignment.objects.create(user=user, crew=crew1, role=role)
    models.CrewAssignment.objects.create(user=user, crew=crew2, role=role)

    am = AvailabilityManager.with_application_form(application_form)

    assert am.get_game_count_for_user(user) == 2
    assert am.get_game_count_for_user(user2) == 0

    assert am.game_counts_by_user == {user.id: 2, user2.id: 0}


def test_get_application_counts_and_get_potential_applications(db):
    application_form = ApplicationFormFactory(
        application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT
    )
    role_group = application_form.role_groups.first()
    assert role_group

    for status in models.IN_PROGRESS_STATUSES:
        ApplicationFactory(
            form=application_form, status=status, roles=role_group.roles.all()
        )
    for status in models.CLOSED_STATUSES:
        ApplicationFactory(
            form=application_form, status=status, roles=role_group.roles.all()
        )

    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    game = GameFactory(event=application_form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role_group
    )

    am = AvailabilityManager.with_application_form(application_form)

    available_count, potential_count = am.get_application_counts(
        crew, game, role_group.roles.first()
    )
    assert potential_count == available_count == len(models.IN_PROGRESS_STATUSES)

    assert len(
        am.get_potential_applications(crew, game, role_group.roles.first())
    ) == len(models.IN_PROGRESS_STATUSES)


def test_get_application_entries(db):
    application_form = ApplicationFormFactory(
        application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT
    )
    role_group = application_form.role_groups.first()
    assert role_group

    for status in models.IN_PROGRESS_STATUSES:
        ApplicationFactory(
            form=application_form, status=status, roles=role_group.roles.all()
        )

    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    game = GameFactory(event=application_form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role_group
    )

    am = AvailabilityManager.with_application_form(application_form)

    entries = am.get_application_entries(crew, game, role_group.roles.first())
    assert len(entries) == len(models.IN_PROGRESS_STATUSES)
    for entry in entries:
        assert entry.availability_status == ConflictKind.NONE
        assert entry.conflicting_roles is None


def test_get_swappable_assignments(db):
    application_form = ApplicationFormFactory(
        application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT
    )
    role_group = application_form.role_groups.first()
    assert role_group

    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    game = GameFactory(event=application_form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role_group
    )

    user = UserFactory()
    role1 = role_group.roles.first()
    role2 = RoleFactory(role_group=role_group)
    models.CrewAssignment.objects.create(user=user, crew=crew, role=role1)

    am = AvailabilityManager.with_application_form(application_form)
    swappable = am.get_swappable_assignments(user, crew, game, role2)

    # Should find role1 as swappable (same crew, same times, both exclusive)
    assert len(swappable) == 1
    assert swappable[0].role == role1
    assert swappable[0].crew == crew

    # Check for role1 (same role user already has) - should be swappable (self-swap)
    swappable_same = am.get_swappable_assignments(user, crew, game, role1)
    assert len(swappable_same) == 1
    assert swappable_same[0].role == role1

    # TODO: expand this test.


def test_get_application_for_user(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.APPLIED,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )

    am = AvailabilityManager.with_application_form(application.form)

    assert am.get_application_for_user(application.user) == application


def test_get_application_for_user__withdrawn(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.WITHDRAWN,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )

    am = AvailabilityManager.with_application_form(application.form)

    assert am.get_application_for_user(application.user) is None


def test_get_application_by_id(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.APPLIED,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )

    am = AvailabilityManager.with_application_form(application.form)

    assert am.get_application_by_id(application.id) == application


def test_get_application_by_id__withdrawn(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.WITHDRAWN,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )

    am = AvailabilityManager.with_application_form(application.form)

    assert am.get_application_by_id(application.id) is None


def test_get_application_for_assignment(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.APPLIED,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    assert role
    crew = CrewFactory(event=application.form.event, role_group=role.role_group)
    ca = models.CrewAssignment.objects.create(
        user=application.user, crew=crew, role=role
    )
    other_role = RoleFactory(role_group=role.role_group)
    ca_no_user = models.CrewAssignment.objects.create(
        crew=crew, role=other_role, user=None
    )

    am = AvailabilityManager.with_application_form(application.form)

    app = am.get_application_for_assignment(ca)
    assert app == application
    app_none = am.get_application_for_assignment(ca_no_user)
    assert app_none is None


def test_get_assignment(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.APPLIED,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    assert role
    crew = CrewFactory(event=application.form.event, role_group=role.role_group)
    ca = models.CrewAssignment.objects.create(
        user=application.user, crew=crew, role=role
    )

    am = AvailabilityManager.with_application_form(application.form)

    found = am.get_assignment(role, crew)
    assert found == ca

    # Test with role that has no assignment
    other_role = RoleFactory(role_group=role.role_group)
    found_none = am.get_assignment(other_role, crew)
    assert found_none is None


def test_set_assignment__open_slot(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.APPLIED,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    assert role
    crew = CrewFactory(event=application.form.event, role_group=role.role_group)

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, application.user)

    assert crew.get_assignments_by_role_id()[role.id].user == application.user
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.ASSIGNMENT_PENDING


def test_set_assignment__replace_existing(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    other_application = ApplicationFactory(
        form=application.form, status=models.ApplicationStatus.APPLIED, roles=[role]
    )
    crew = CrewFactory(event=application.form.event, role_group=role.role_group)
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    assert not models.CrewAssignment.objects.filter(user=application.user).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING


def test_set_assignment__removes_existing_assignment(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    crew = CrewFactory(event=application.form.event, role_group=role.role_group)
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, None)

    assert not models.CrewAssignment.objects.filter(user=application.user).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    assert crew.get_assignments_by_role_id()[role.id].user is None


def test_set_crew_assignment__assign_crew_over_individual_assignments(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    static_crew = CrewFactory(
        kind=models.CrewKind.GAME_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    # Swapping roles requires the Crew have a non-None
    # get_context()
    game = GameFactory(event=application.form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role.role_group
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)

    am = AvailabilityManager.with_application_form(application.form)
    am.set_crew_assignment(role.role_group, static_crew, game=game)

    # All CrewAssignments from the override crew should be removed
    # There should be no blanking overrides
    assert not models.CrewAssignment.objects.filter(crew=crew).exists()


def test_set_crew_assignment__assign_crew_with_unavailable_member_blanks(db):
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    static_crew = CrewFactory(
        kind=models.CrewKind.GAME_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    # Swapping roles requires the Crew have a non-None
    # get_context()
    game = GameFactory(event=application.form.event)
    rgca = models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role.role_group
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)

    static_crew_game = GameFactory(event=application.form.event)

    am = AvailabilityManager.with_application_form(application.form)
    am.set_crew_assignment(role.role_group, static_crew, game=static_crew_game)
    static_rgca = models.RoleGroupCrewAssignment.objects.get(crew=static_crew)

    assert rgca.effective_crew_by_role_id()[role.id].user == application.user
    assert static_rgca.effective_crew_by_role_id()[role.id].user is None


def test_set_assignment__swap_roles_one_to_one_on_override_crew(db):
    # Arrange
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    other_role = RoleFactory(role_group=role.role_group)
    other_application = ApplicationFactory(
        form=application.form,
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        roles=[role, other_role],
    )
    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    # Swapping roles requires the Crew have a non-None
    # get_context()
    game = GameFactory(event=application.form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role.role_group
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=crew, role=other_role
    )

    # Act
    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    # Assert
    assert not models.CrewAssignment.objects.filter(user=application.user).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING
    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    assert crew.get_assignments_by_role_id()[other_role.id].user is None


def test_set_assignment__swap_roles_one_to_one_on_override_crew_with_nonexclusive(db):
    # Arrange
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    other_role = RoleFactory(role_group=role.role_group)
    nonexclusive_role = RoleFactory(role_group=role.role_group, nonexclusive=True)
    other_application = ApplicationFactory(
        form=application.form,
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        roles=[role, other_role],
    )
    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    # Swapping roles requires the Crew have a non-None
    # get_context()
    game = GameFactory(event=application.form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, game=game, role_group=role.role_group
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=crew, role=other_role
    )
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=crew, role=nonexclusive_role
    )

    # Act
    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    # Assert
    assert not models.CrewAssignment.objects.filter(user=application.user).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING
    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    assert (
        crew.get_assignments_by_role_id()[nonexclusive_role.id].user
        == other_application.user
    )
    assert crew.get_assignments_by_role_id()[other_role.id].user is None


def test_set_assignment__swap_roles_static_crew_to_override_crew(db):
    # Arrange
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    other_role = RoleFactory(role_group=role.role_group)
    other_application = ApplicationFactory(
        form=application.form,
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        roles=[role, other_role],
    )
    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    static_crew = CrewFactory(
        kind=models.CrewKind.GAME_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    # Swapping roles requires the Crew have a non-None
    # get_context()
    game = GameFactory(event=application.form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, crew=static_crew, game=game, role_group=role.role_group
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=static_crew, role=other_role
    )

    # Act
    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    # Assert
    # Original assignee is unassigned
    assert not models.CrewAssignment.objects.filter(user=application.user).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    # New assignee is in the correct status
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING
    # New assignee is assigned on the override crew
    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    # A blank CrewAssignment covers their role on the static crew.
    assert crew.get_assignments_by_role_id()[other_role.id].user is None
    # Their assignment on the static crew is unchanged.
    assert (
        static_crew.get_assignments_by_role_id()[other_role.id].user
        == other_application.user
    )


def test_set_assignment__swap_roles_static_crew_to_blank(db):
    # DMR: is this testing the right thing?
    # We need to test swapping a user OUT of a slot they occupy
    # via static crew, to see it get blanked.
    # Assign a user to a static crew, then blank the assignment
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    crew = CrewFactory(
        kind=models.CrewKind.GAME_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, None)

    # Assignment should be removed
    assert not models.CrewAssignment.objects.filter(
        user=application.user, crew=crew, role=role
    ).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    # Crew assignment should be blank (user=None)
    assert crew.get_assignments_by_role_id()[role.id].user is None


def test_set_assignment__swap_roles_event_crew(db):
    # Swap roles on an event crew
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    other_role = RoleFactory(role_group=role.role_group)
    other_application = ApplicationFactory(
        form=application.form,
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        roles=[role, other_role],
    )
    crew = CrewFactory(
        kind=models.CrewKind.EVENT_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=crew, role=other_role
    )

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    # Original assignee is unassigned
    assert not models.CrewAssignment.objects.filter(user=application.user).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    # New assignee gets the role
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING
    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    # Other role is now blank
    assert crew.get_assignments_by_role_id()[other_role.id].user is None


def test_set_assignment__swap_roles_static_crew_to_override_crew_keep_nonexclusive(db):
    # Similar to test_set_assignment__swap_roles_static_crew_to_override_crew
    # but with a nonexclusive role that should be kept
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    other_role = RoleFactory(role_group=role.role_group)
    nonexclusive_role = RoleFactory(role_group=role.role_group, nonexclusive=True)
    other_application = ApplicationFactory(
        form=application.form,
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        roles=[role, other_role],
    )
    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    static_crew = CrewFactory(
        kind=models.CrewKind.GAME_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    game = GameFactory(event=application.form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, crew=static_crew, game=game, role_group=role.role_group
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=static_crew, role=other_role
    )
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=static_crew, role=nonexclusive_role
    )

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    # Original assignee is unassigned
    assert not models.CrewAssignment.objects.filter(user=application.user).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    # New assignee is in the correct status
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING
    # New assignee is assigned on the override crew
    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    # A blank CrewAssignment covers their role on the override crew for other_role
    assert crew.get_assignments_by_role_id()[other_role.id].user is None
    # Their nonexclusive role on the static crew is KEPT (not blanked)
    assert (
        static_crew.get_assignments_by_role_id()[nonexclusive_role.id].user
        == other_application.user
    )
    # Their assignment on the static crew for other_role is unchanged
    assert (
        static_crew.get_assignments_by_role_id()[other_role.id].user
        == other_application.user
    )


def test_set_assignment__swap_roles_event_crew_keep_nonexclusive(db):
    # Swap roles on an event crew, keeping a nonexclusive role
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    other_role = RoleFactory(role_group=role.role_group)
    nonexclusive_role = RoleFactory(role_group=role.role_group, nonexclusive=True)
    other_application = ApplicationFactory(
        form=application.form,
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        roles=[role, other_role],
    )
    crew = CrewFactory(
        kind=models.CrewKind.EVENT_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    models.CrewAssignment.objects.create(user=application.user, crew=crew, role=role)
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=crew, role=other_role
    )
    models.CrewAssignment.objects.create(
        user=other_application.user, crew=crew, role=nonexclusive_role
    )

    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    # Original assignee is unassigned
    assert not models.CrewAssignment.objects.filter(user=application.user).exists()
    application.refresh_from_db()
    assert application.status == models.ApplicationStatus.APPLIED
    # New assignee gets the role
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING
    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    # Other exclusive role is now blank
    assert crew.get_assignments_by_role_id()[other_role.id].user is None
    # Nonexclusive role is KEPT
    assert (
        crew.get_assignments_by_role_id()[nonexclusive_role.id].user
        == other_application.user
    )


def test_set_assignment__static_crew_override_replace_blank_with_original(db):
    # Test replacing a blank override assignment with a new user
    # First, set up a static crew with an assignment
    application = ApplicationFactory(
        status=models.ApplicationStatus.ASSIGNMENT_PENDING,
        form__application_kind=models.ApplicationKind.ASSIGN_ONLY,
    )
    role = application.roles.first()
    static_crew = CrewFactory(
        kind=models.CrewKind.GAME_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    models.CrewAssignment.objects.create(
        user=application.user, crew=static_crew, role=role
    )

    # Create an override crew and assign it to a game, blanking the static crew assignment
    crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application.form.event,
        role_group=role.role_group,
    )
    game = GameFactory(event=application.form.event)
    models.RoleGroupCrewAssignment.objects.create(
        crew_overrides=crew, crew=static_crew, game=game, role_group=role.role_group
    )
    # Blank the override (user=None)
    models.CrewAssignment.objects.create(crew=crew, role=role, user=None)

    # Now assign a new user to the override crew
    other_application = ApplicationFactory(
        form=application.form,
        status=models.ApplicationStatus.APPLIED,
        roles=[role],
    )
    am = AvailabilityManager.with_application_form(application.form)
    am.set_assignment(role, crew, other_application.user)

    # The blank override should be replaced with the new user
    assert crew.get_assignments_by_role_id()[role.id].user == other_application.user
    # The static crew assignment should still exist (it was blanked by the override)
    assert static_crew.get_assignments_by_role_id()[role.id].user == application.user
    # Other application status updated
    other_application.refresh_from_db()
    assert other_application.status == models.ApplicationStatus.ASSIGNMENT_PENDING


def test_set_crew_assignment(db):
    # Test set_crew_assignment method
    application_form = ApplicationFormFactory()
    role_group = application_form.role_groups.first()
    assert role_group

    # Create a static crew
    static_crew = CrewFactory(
        kind=models.CrewKind.GAME_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    # Create an override crew
    override_crew = CrewFactory(
        kind=models.CrewKind.OVERRIDE_CREW,
        event=application_form.event,
        role_group=role_group,
    )
    game = GameFactory(event=application_form.event)
    # Create RoleGroupCrewAssignment with static crew
    rgca = models.RoleGroupCrewAssignment.objects.create(
        crew=static_crew, game=game, role_group=role_group
    )

    # Create an application for the user
    application = ApplicationFactory(
        form=application_form,
        status=models.ApplicationStatus.APPLIED,
        roles=[role_group.roles.first()],
    )
    user = application.user
    role = role_group.roles.first()

    # Assign the user to the static crew
    models.CrewAssignment.objects.create(user=user, crew=static_crew, role=role)

    am = AvailabilityManager.with_application_form(application_form)
    # Assign the override crew to the game
    am.set_crew_assignment(role_group, override_crew, game)

    # The RoleGroupCrewAssignment should now have the override crew
    rgca.refresh_from_db()
    assert rgca.crew_overrides == override_crew
    # The static crew should be removed from the RoleGroupCrewAssignment
    assert rgca.crew is None
    # The override crew should have a blank assignment for the role
    assert override_crew.get_assignments_by_role_id()[role.id].user is None
    # The static crew assignment should still exist (but is overridden)
    assert static_crew.get_assignments_by_role_id()[role.id].user == user
