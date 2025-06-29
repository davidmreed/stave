from typing import Iterable
from datetime import datetime
from collections import defaultdict
from uuid import UUID
from . import models
from dataclasses import dataclass
import functools


@dataclass
class UserAvailabilityEntry:
    crew: models.Crew
    exclusive: bool

    def overlaps(self, other: "UserAvailabilityEntry") -> bool:
        if self.crew.kind != other.crew.kind:
            return False

        if self.crew.id == other.crew.id:
            return self.exclusive and other.exclusive

        match self.crew.kind:
            case models.CrewKind.OVERRIDE_CREW:
                time_overlap = (
                    self.crew.get_context().start_time
                    < other.crew.get_context().end_time
                ) and (
                    self.crew.get_context().end_time
                    > other.crew.get_context().start_time
                )
                return time_overlap
            case models.CrewKind.GAME_CREW | models.CrewKind.EVENT_CREW:
                return True


class AvailabilityManager:
    application_form: models.ApplicationForm
    applications: dict[UUID, dict[str, Iterable[models.Application]]]

    @classmethod
    def with_role_group_and_roles(
        klass,
        application_form: models.ApplicationForm,
        role_group: models.RoleGroup,
        roles: Iterable[models.Role],
    ) -> "AvailabilityManager":
        am = AvailabilityManager()
        am.application_form = application_form
        am.applications = {
            role_group.id: am._load_applications_for_role_group(role_group, roles)
        }

        return am

    @classmethod
    def with_role_groups(
        klass,
        application_form: models.ApplicationForm,
        role_groups: Iterable[models.RoleGroup],
    ) -> "AvailabilityManager":
        am = AvailabilityManager()
        am.application_form = application_form
        am.applications = am._load_applications_for_role_groups(role_groups)

        return am

    def _load_applications_for_role_groups(
        self, role_groups: Iterable[models.RoleGroup]
    ) -> dict[UUID, dict[str, Iterable[models.Application]]]:
        return {
            role_group.id: self._load_applications_for_role_group(
                role_group, role_group.roles.all()
            )
            for role_group in role_groups
        }

    def _load_applications_for_role_group(
        self, role_group: models.RoleGroup, roles: Iterable[models.Role]
    ) -> dict[str, Iterable[models.Application]]:
        # If our input roles and role_group are not sensical, this query will be empty.
        # No risk of incoherent output data.
        applications = self.application_form.applications.filter(
            roles__in=roles, roles__role_group_id=role_group.id
        ).distinct()

        # Filter based on our application model.
        if (
            self.application_form.application_kind
            == models.ApplicationKind.CONFIRM_ONLY
        ):
            applications = applications.filter(
                status__in=[
                    models.ApplicationStatus.APPLIED,
                    models.ApplicationStatus.INVITED,
                    models.ApplicationStatus.CONFIRMED,
                ]
            )
        elif (
            self.application_form.application_kind
            == models.ApplicationKind.CONFIRM_THEN_ASSIGN
        ):
            applications = applications.filter(
                status=models.ApplicationStatus.CONFIRMED
            )

        result = defaultdict(list)
        for application in applications:
            app_roles = application.roles.all()
            for role in roles:
                if role in app_roles:
                    result[role.name].append(application)

        return result

    @property
    @functools.cache
    def static_crews(self):
        return self.application_form.static_crews().prefetch_assignments()

    @property
    @functools.cache
    def event_crews(self):
        return self.application_form.event_crews().prefetch_assignments()

    @property
    @functools.cache
    def user_availability(self) -> dict[UUID, list[UserAvailabilityEntry]]:
        # Grab all of the crew assignments for this event.
        rgcas = (
            models.RoleGroupCrewAssignment.objects.filter(
                game__event=self.application_form.event
            )
            .prefetch_related("crew__assignments", "crew_overrides__assignments")
            .select_related("game")
        )
        user_assigned_times_map = defaultdict(list)
        for rgca in rgcas:
            effective_crew = rgca.effective_crew_by_role_id().values()
            for assignment in effective_crew:
                # We squash all effective game assignments to appear
                # as part of the override crew. This ensures we
                # catch conflicts between the assigned static crew
                # and the overrides.
                user_assigned_times_map[assignment.user_id].append(
                    UserAvailabilityEntry(
                        crew=rgca.crew_overrides,
                        exclusive=not assignment.role.nonexclusive,
                    )
                )

        return user_assigned_times_map

    @property
    @functools.cache
    def user_event_availability(self) -> dict[UUID, list[UserAvailabilityEntry]]:
        user_event_map = defaultdict(list)
        for crew in self.event_crews:
            for assignment in crew.assignments.all():
                user_event_map[assignment.user_id].append(
                    UserAvailabilityEntry(
                        crew,
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
                        not assignment.role.nonexclusive,
                    )
                )

        return user_static_map

    def get_application_counts(
        self, crew: models.Crew, role: models.Role
    ) -> tuple[int, int]:
        return (
            len(self.get_available_applications(crew, role)),
            len(self.get_all_applications(crew, role)),
        )

    def get_all_applications(
        self, crew: models.Crew, role: models.Role
    ) -> list[models.Application]:
        return self._filter_for_basic_availability(
            self.applications[role.role_group_id][role.name], crew
        )

    def get_available_applications(
        self, crew: models.Crew, role: models.Role
    ) -> list[models.Application]:
        return self._filter_for_already_assigned_users(
            self.get_all_applications(crew, role),
            crew,
            role,
        )

    # Filter methods MUST NOT hit the database - use only cached data
    def _filter_for_basic_availability(
        self,
        applications: Iterable[models.Application],
        crew: models.Crew,
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
                    if str(crew.get_context().start_time.date())
                    in app.availability_by_day
                ]

            elif (
                self.application_form.application_availability_kind
                == models.ApplicationAvailabilityKind.BY_GAME
            ):
                return [
                    app
                    for app in applications
                    if crew.get_context() in app.availability_by_game.all()
                ]

        return applications

    def _filter_for_already_assigned_users(
        self,
        applications: Iterable[models.Application],
        crew: models.Crew,
        role: models.Role,
    ) -> Iterable[models.Application]:
        entry = UserAvailabilityEntry(
            crew,
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
