from dataclasses import dataclass
from typing import Any
from uuid import UUID

from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet

from stave import forms, models


@dataclass
class ApplicationActionsInputs:
    user: models.User
    can_manage_event: bool
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
    form: models.ApplicationForm | None
    role_group: models.RoleGroup
    crew: models.Crew
    crew_assignments: dict[UUID, models.CrewAssignment]
    editable: bool
    focus_user_id: UUID | None


@dataclass
class CrewBuilderDetailInputs:
    event: models.Event
    form: models.ApplicationForm
    role: models.Role
    game: models.Game | None
    applications: list[models.Application]


@dataclass
class CrewBuilderInputs:
    event: models.Event
    form: models.ApplicationForm | None  # Not required for schedule view only
    role_groups: QuerySet[models.RoleGroup]
    games: QuerySet[models.Game]
    focus_user_id: UUID | None
    static_crews: dict[UUID, models.Crew]
    event_crews: dict[UUID, models.Crew]
    allow_static_crews: dict[UUID, bool]
    any_static_crew_role_groups: bool
    editable: bool


@dataclass
class LeagueDetailViewInputs:
    events: QuerySet[models.Event]


@dataclass
class ViewApplicationContext:
    app_form: models.ApplicationForm
    form: forms.ApplicationForm | None
    application: models.Application | None
    ApplicationStatus: type
    editable: bool


@dataclass
class FormApplicationsInputs:
    form: models.ApplicationForm
    applications: dict[models.ApplicationStatus, list[models.Application]]
    ApplicationStatus: type
    invited_unsent_count: int


@dataclass
class SendEmailInputs:
    kind: models.SendEmailContextType
    application_form: models.ApplicationForm
    email_form: forms.SendEmailForm
    members: QuerySet[models.User]
    redirect_url: str | None


@dataclass
class TemplateSelectorInputs:
    templates: QuerySet[models.LeagueTemplate] | QuerySet[models.EventTemplate]
    object_type: str
    require_template_selection_first: bool
    selected_template: models.LeagueTemplate | models.EventTemplate | None = None


@dataclass
class EventDetailInputs:
    event: models.Event
    application_forms: QuerySet[models.ApplicationForm] | None


@dataclass
class EventCardInputs(EventDetailInputs):
    user: models.User | AnonymousUser
    show_host: bool
    show_details: bool
    show_forms: bool
    show_games: bool


@dataclass
class ParentChildCreateUpdateInputs:
    object: Any
    form: forms.ParentChildForm
    view_url: str
    parent_name: str
    child_name: str
    child_name_plural: str


@dataclass
class StaffListInputs:
    users: list[models.User]
    event: models.Event
