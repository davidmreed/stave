from dataclasses import dataclass, fields
from typing import Tuple
from uuid import UUID

from django.core.paginator import Page
from django.db.models import QuerySet
from django.http import HttpRequest

from stave import forms, models, avail


def to_dict(obj) -> dict:
    return {field.name: getattr(obj, field.name) for field in fields(obj)}


@dataclass
class ApplicationActionsInputs:
    user: models.User
    can_manage_event: bool
    application: models.Application
    ApplicationStatus: type
    include_view: bool
    minimal: bool = False


@dataclass
class ApplicationTableInputs:
    form: models.ApplicationForm


@dataclass
class ApplicationTableRowInputs:
    form: models.ApplicationForm
    entry: avail.ApplicationEntry


@dataclass
class CrewEditorInputs:
    form: models.ApplicationForm | None
    role_group: models.RoleGroup
    crew: models.Crew
    crew_assignments: dict[UUID, models.CrewAssignment]
    editable: bool
    focus_user_id: UUID | None
    counts: dict[str, tuple[int, int]]


@dataclass
class CrewBuilderDetailInputs:
    event: models.Event
    form: models.ApplicationForm
    role: models.Role
    game: models.Game | None
    applications: list[avail.ApplicationEntry]
    ConflictKind: type = avail.ConflictKind


@dataclass
class CrewBuilderInputs:
    event: models.Event
    form: models.ApplicationForm | None  # Not required for schedule view only
    role_groups: QuerySet[models.RoleGroup]
    games: QuerySet[models.Game]
    focus_user_id: UUID | None
    static_crews: dict[UUID, models.Crew]
    event_crews: dict[UUID, models.Crew]
    allow_static_crews: bool
    editable: bool
    counts: dict[models.Game | models.Event | None, dict[str, tuple[int, int]]]
    show_day_header: bool


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
    applications_action: list[avail.ApplicationEntry]
    applications_inprogress: list[avail.ApplicationEntry]
    applications_staffed: list[avail.ApplicationEntry]
    applications_closed: list[avail.ApplicationEntry]
    ApplicationStatus: type


@dataclass
class SendEmailInputs:
    kind: models.SendEmailContextType
    application_form: models.ApplicationForm
    email_form: forms.SendEmailForm
    email_recipients_form: forms.SendEmailRecipientsForm
    redirect_url: str | None
    merge_fields: list[models.MergeField]
    recipient_count: int


@dataclass
class MessageTemplateEditInputs:
    form: forms.MessageTemplateForm
    merge_fields: list[models.MergeField]


@dataclass
class TemplateSelectorInputs:
    templates: QuerySet[models.LeagueTemplate] | QuerySet[models.EventTemplate]
    object_type: str
    require_template_selection_first: bool
    selected_template: models.LeagueTemplate | models.EventTemplate | None = None
    disclaimer: str | None = None


@dataclass
class EventDetailInputs:
    event: models.Event
    application_forms: QuerySet[models.ApplicationForm] | None


@dataclass
class ParentChildCreateUpdateInputs:
    form: forms.ParentChildForm
    parent_name: str
    child_name: str
    child_name_plural: str
    allow_child_adds: bool
    allow_child_deletes: bool
    child_variants: list[Tuple[str, str, dict[str, str]]] | None


@dataclass
class ParentChildCreateUpdateTimezoneInputs(ParentChildCreateUpdateInputs):
    time_zone: str


@dataclass
class ApplicationFormCreateUpdateInputs(ParentChildCreateUpdateTimezoneInputs):
    event: models.Event


@dataclass
class StaffListInputs:
    users: list[models.User]
    event: models.Event


@dataclass
class CalendarInputs:
    url: str


@dataclass
class CommCenterInputs:
    pending_invitation: QuerySet[models.Application]
    pending_rejection: QuerySet[models.Application]
    pending_assignment: QuerySet[models.Application]
    application_form: models.ApplicationForm
    redirect_url: str


@dataclass
class StaffingHeaderInputs:
    form: models.ApplicationForm
    request: HttpRequest


@dataclass
class HomeInputs:
    application_forms: Page
    applications: Page
    events: Page
    leagues: Page
    league_groups: Page
    subscribed_leagues: int
    subscribed_league_groups: int


@dataclass
class LeagueGroupInputs:
    events: Page
