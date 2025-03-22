from dataclasses import dataclass
from uuid import UUID

from django.db.models import QuerySet
from django.http import HttpRequest

from stave import forms, models


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


@dataclass
class LeagueDetailViewInputs:
    events: QuerySet[models.Event]


@dataclass
class ViewApplicationContext:
    form: models.ApplicationForm
    application: models.Application | None
    ApplicationStatus: type
    user_data: dict[str, str]
    responses_by_id: dict[UUID, models.ApplicationResponse]
    editable: bool
    profile_form: forms.ProfileForm | None


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
    selected_template: models.LeagueTemplate | models.EventTemplate | None
    require_template_selection_first: bool


@dataclass
class EventDetailInputs:
    event: models.Event
    application_forms: QuerySet[models.ApplicationForm]
