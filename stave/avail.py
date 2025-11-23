import functools
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from uuid import UUID

from django.db.models import Prefetch, QuerySet

from . import models


@dataclass
class UserAvailabilityEntry:
    crew: models.Crew
    # Denormalize these off the crew's Game
    # to avoid excess queries.
    start_time: datetime | None
    end_time: datetime | None
    exclusive: bool

    def overlaps(self, other: "UserAvailabilityEntry") -> bool:
        if self.crew.kind != other.crew.kind:
            return False

        if self.crew.id == other.crew.id:
            return self.exclusive and other.exclusive

        match self.crew.kind:
            case models.CrewKind.OVERRIDE_CREW:
                time_overlap = (self.start_time < other.end_time) and (
                    self.end_time > other.start_time
                )
                return time_overlap
            case models.CrewKind.GAME_CREW | models.CrewKind.EVENT_CREW:
                return True


class ScheduleManager:
    event: models.Event

    def __init__(self, event: models.Event, role_groups: QuerySet[models.RoleGroup]):
        self.event = event
        self.event = (
            models.Event.objects.filter(id=event.id)
            .prefetch_related(
                Prefetch("role_groups", queryset=role_groups),
                "role_groups__roles",
                Prefetch(
                    "games",
                    queryset=models.Game.objects.filter(
                        role_groups__in=role_groups
                    ).distinct(),
                ),
                Prefetch(
                    "games__role_group_crew_assignments",
                    queryset=models.RoleGroupCrewAssignment.objects.filter(
                        role_group__in=role_groups
                    ).select_related("crew", "role_group"),
                ),
                "games__role_group_crew_assignments__crew__role_group__roles",
                "games__role_group_crew_assignments__crew_overrides__role_group__roles",
                Prefetch(
                    "games__role_group_crew_assignments__crew__assignments",
                    queryset=models.CrewAssignment.objects.select_related(
                        "user", "role", "role__role_group"
                    ),
                ),
                Prefetch(
                    "games__role_group_crew_assignments__crew_overrides__assignments",
                    queryset=models.CrewAssignment.objects.select_related(
                        "user", "role", "role__role_group"
                    ),
                ),
                Prefetch(
                    "crews",
                    queryset=models.Crew.objects.filter(
                        role_group__in=role_groups
                    ).select_related("role_group"),
                ),
                "crews__role_group__roles",
                Prefetch(
                    "crews__assignments",
                    queryset=models.CrewAssignment.objects.select_related(
                        "user", "role", "role__role_group"
                    ),
                ),
            )
            .select_related("league")
        ).first()

    @property
    @functools.cache
    def static_crews(self) -> list[models.Crew]:
        return [
            crew
            for crew in self.event.crews.all()
            if crew.kind == models.CrewKind.GAME_CREW
        ]

    @property
    @functools.cache
    def event_crews(self) -> list[models.Crew]:
        return [
            crew
            for crew in self.event.crews.all()
            if crew.kind == models.CrewKind.EVENT_CREW
        ]


class AvailabilityManager:
    application_form: models.ApplicationForm

    @classmethod
    def with_application_form(
        klass, application_form: models.ApplicationForm
    ) -> "AvailabilityManager":
        # Filter based on our application model.
        application_qs = models.Application.objects.exclude(
            status__in=[
                models.ApplicationStatus.WITHDRAWN,
                models.ApplicationStatus.DECLINED,
                models.ApplicationStatus.REJECTED,
                models.ApplicationStatus.REJECTION_PENDING,
            ]
        )
        application_form: models.ApplicationForm = (
            models.ApplicationForm.objects.filter(id=application_form.id)
            .prefetch_related(
                "role_groups",
                "role_groups__roles",
                Prefetch("applications", queryset=application_qs),
                Prefetch(
                    "applications__roles",
                    queryset=models.Role.objects.select_related("role_group"),
                ),
                Prefetch(
                    "applications__availability_by_game",
                ),
                Prefetch(
                    "event__games",
                    queryset=models.Game.objects.filter(
                        role_groups__in=application_form.role_groups.all()
                    ).distinct(),
                ),
                Prefetch(
                    "event__games__role_group_crew_assignments",
                    queryset=models.RoleGroupCrewAssignment.objects.filter(
                        role_group__in=application_form.role_groups.all()
                    ).select_related("crew", "role_group"),
                ),
                "event__games__role_group_crew_assignments__crew__role_group__roles",
                "event__games__role_group_crew_assignments__crew_overrides__role_group__roles",
                Prefetch(
                    "event__games__role_group_crew_assignments__crew__assignments",
                    queryset=models.CrewAssignment.objects.select_related(
                        "user", "role", "role__role_group"
                    ),
                ),
                Prefetch(
                    "event__games__role_group_crew_assignments__crew_overrides__assignments",
                    queryset=models.CrewAssignment.objects.select_related(
                        "user", "role", "role__role_group"
                    ),
                ),
                Prefetch(
                    "event__crews",
                    queryset=models.Crew.objects.filter(
                        role_group__in=application_form.role_groups.all()
                    ).select_related("role_group"),
                ),
                "event__crews__role_group__roles",
                Prefetch(
                    "event__crews__assignments",
                    queryset=models.CrewAssignment.objects.select_related(
                        "user", "role", "role__role_group"
                    ),
                ),
            )
            .select_related("event", "event__league")
        ).first()
        am = AvailabilityManager()
        am.application_form = application_form

        return am

    @property
    @functools.cache
    def applications(self) -> list[models.Application]:
        return list(self.application_form.applications.all())

    @property
    @functools.cache
    def applications_by_status(
        self,
    ) -> dict[models.ApplicationStatus, list[models.Application]]:
        apps = {}
        for application in self.applications:
            apps.setdefault(application.status, []).append(application)

        return apps

    @functools.cache
    def get_applications_in_statuses(
        self, statuses: tuple[models.ApplicationStatus]
    ) -> list[models.Application]:
        apps = []
        for status in statuses:
            apps.extend(self.applications_by_status.get(status, []))

        return sorted(apps, key=lambda a: a.user.preferred_name)

    @property
    @functools.cache
    def applications_by_role_group(
        self,
    ) -> dict[UUID, dict[str, list[models.Application]]]:
        applications = defaultdict(lambda: defaultdict(list))
        for application in self.application_form.applications.all():
            for role in application.roles.all():
                applications[role.role_group_id][role.name].append(application)

        return applications

    @property
    @functools.cache
    def static_crews(self) -> list[models.Crew]:
        return [
            crew
            for crew in self.application_form.event.crews.all()
            if crew.kind == models.CrewKind.GAME_CREW
        ]

    @property
    @functools.cache
    def event_crews(self) -> list[models.Crew]:
        return [
            crew
            for crew in self.application_form.event.crews.all()
            if crew.kind == models.CrewKind.EVENT_CREW
        ]

    @property
    @functools.cache
    def user_availability(self) -> dict[UUID, list[UserAvailabilityEntry]]:
        user_assigned_times_map = defaultdict(list)

        for game in self.application_form.event.games.all():
            for rgca in game.role_group_crew_assignments.all():
                effective_crew = rgca.effective_crew_by_role_id().values()
                for assignment in effective_crew:
                    # We squash all effective game assignments to appear
                    # as part of the override crew. This ensures we
                    # catch conflicts between the assigned static crew
                    # and the overrides.
                    user_assigned_times_map[assignment.user_id].append(
                        UserAvailabilityEntry(
                            crew=rgca.crew_overrides,
                            start_time=game.start_time,
                            end_time=game.end_time,
                            exclusive=not assignment.role.nonexclusive,
                        )
                    )

        return user_assigned_times_map

    def get_game_count_for_user(self, user: models.User) -> int:
        # Note that user_availability only includes game crew assignments.

        # This expression ensures that multiple assignments in the same
        # time window get coalesced.
        return len(
            set(
                (a.start_time, a.end_time)
                for a in self.user_availability.get(user.id, [])
            )
        )

    @property
    @functools.cache
    def game_counts_by_user(self) -> dict[UUID, int]:
        return {
            a.user.id: self.get_game_count_for_user(a.user) for a in self.applications
        }

    @property
    @functools.cache
    def user_event_availability(self) -> dict[UUID, list[UserAvailabilityEntry]]:
        user_event_map = defaultdict(list)
        for crew in self.event_crews:
            for assignment in crew.assignments.all():
                user_event_map[assignment.user_id].append(
                    UserAvailabilityEntry(
                        crew,
                        None,
                        None,
                        not assignment.role.nonexclusive,
                    )
                )

        return user_event_map

    @property
    @functools.cache
    def user_static_crew_availability(self) -> dict[UUID, list[UserAvailabilityEntry]]:
        user_static_map = defaultdict(list)
        for crew in self.static_crews:
            for assignment in crew.assignments.all():
                user_static_map[assignment.user_id].append(
                    UserAvailabilityEntry(
                        crew,
                        None,
                        None,
                        not assignment.role.nonexclusive,
                    )
                )

        return user_static_map

    def get_application_counts(
        self, crew: models.Crew, game: models.Game | None, role: models.Role
    ) -> tuple[int, int]:
        return (
            len(self.get_available_applications(crew, game, role)),
            len(self.get_all_applications(crew, game, role)),
        )

    @functools.cache
    def get_all_applications(
        self, crew: models.Crew, game: models.Game | None, role: models.Role
    ) -> list[models.Application]:
        return self._filter_for_basic_availability(
            self.applications_by_role_group[role.role_group_id][role.name], crew, game
        )

    @functools.cache
    def get_swappable_applications(self, crew: models.Crew, game: models.Game | None, role: models.Role) -> list[models.Application]:
        """To be swappable, all overlapping assignments have to be in Role Groups managed on the same
        Application Form, and cannot be part of a static crew. If we swapped out of a static crew,
        we'd have no way to mark the slot empty."""
        ...

    @functools.cache
    def get_available_applications(
        self, crew: models.Crew, game: models.Game | None, role: models.Role
    ) -> list[models.Application]:
        return self._filter_for_already_assigned_users(
            self.get_all_applications(crew, game, role),
            crew,
            game,
            role,
        )

    # Filter methods MUST NOT hit the database - use only cached data
    def _filter_for_basic_availability(
        self,
        applications: Iterable[models.Application],
        crew: models.Crew,
        game: models.Game | None,
    ) -> Iterable[models.Application]:
        # Only game crews require this check.
        # Event crew forms aren't allowed to use BY_DAY, and static crews
        # don't have basic availability.
        if crew.kind == models.CrewKind.OVERRIDE_CREW:
            if (
                self.application_form.application_availability_kind
                == models.ApplicationAvailabilityKind.BY_DAY
            ):
                return [
                    app
                    for app in applications
                    if str(game.start_time.date()) in app.availability_by_day
                ]

            elif (
                self.application_form.application_availability_kind
                == models.ApplicationAvailabilityKind.BY_GAME
            ):
                return [
                    app
                    for app in applications
                    if game in app.availability_by_game.all()
                ]

        return applications

    def _filter_for_already_assigned_users(
        self,
        applications: Iterable[models.Application],
        crew: models.Crew,
        game: models.Game | None,
        role: models.Role,
    ) -> Iterable[models.Application]:
        entry = UserAvailabilityEntry(
            crew,
            game.start_time if game else None,
            game.end_time if game else None,
            not role.nonexclusive,
        )

        match crew.kind:
            case models.CrewKind.OVERRIDE_CREW:
                avail = self.user_availability
            case models.CrewKind.EVENT_CREW:
                avail = self.user_event_availability
            case models.CrewKind.GAME_CREW:
                avail = self.user_static_crew_availability

        return list(
            filter(
                lambda app: not any(t.overlaps(entry) for t in avail[app.user_id]),
                applications,
            )
        )
