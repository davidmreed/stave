from stave import models
from dataclasses import dataclass
from uuid import UUID
from django.http import HttpRequest


@dataclass
class ApplicationActionsInputs:
    user: models.User
    application: models.Application
    ApplicationStatus: type
    include_view: bool


@dataclass
class ApplicationTableInputs:
    form: models.ApplicationForm


@dataclass
class ApplicationTableRowInputs:
    form: models.ApplicationForm
    application: models.Application


@dataclass
class CrewEditorInputs:
    form: models.ApplicationForm
    role_group: models.RoleGroup
    crew: models.Crew
    crew_assignments: dict[UUID, models.CrewAssignment]


@dataclass
class CrewBuilderDetailInputs:
    event: models.Event
    form: models.ApplicationForm
    role: models.Role
    game: models.Game | None
    applications: list[models.Application]


@dataclass
class CrewBuilderInputs:
    form: models.ApplicationForm
    request: HttpRequest
    static_crews: dict[UUID, models.Crew]
    event_crews: dict[UUID, models.Crew]
    allow_static_crews: dict[UUID, bool]
    any_static_crew_role_groups: bool
