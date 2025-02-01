import uuid
from datetime import date, timedelta
import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preferred_name = models.CharField(max_length=256)
    pronouns = models.CharField(max_length=32, blank=True, null=True)
    game_history_url = models.URLField(blank=True, null=True)

    def __str__(self) -> str:
        return self.preferred_name

class RoleGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    requires_profile_fields :models.JSONField[list[str]]= models.JSONField(default=list, blank=True) # TODO: this field's probably in the wrong place.

    roles: models.Manager["Role"]

    def __str__(self) -> str:
        return self.name

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_group = models.ForeignKey(RoleGroup, related_name="roles", on_delete=models.CASCADE)
    order_key = models.IntegerField()
    name = models.CharField(max_length=256)
    nonexclusive = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=["role_group", "order_key"], name="unique_order_key")
                ]
        ordering = ["role_group", "order_key"]

class League(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField()
    name = models.CharField(max_length=256)

    events: models.Manager['Event']

    def __str__(self) -> str:
        return self.name

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=["slug"], name="unique_slug")
                ]
        ordering = ["name"]

class LeagueUserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

class EventTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    role_groups : models.ManyToManyField["EventTemplate", RoleGroup] = models.ManyToManyField(RoleGroup, blank=True)

class Crew(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event: models.ForeignKey['Event'] = models.ForeignKey("Event", related_name="crews", on_delete=models.CASCADE)
    role_group = models.ForeignKey(RoleGroup, related_name="crews", on_delete=models.CASCADE)
    is_override = models.BooleanField(default=False)

    assignments: models.Manager['CrewAssignment']

class CrewAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crew = models.ForeignKey(Crew, related_name="assignments",  on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="crews", null=True, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, related_name="crew_assignments", on_delete=models.CASCADE)
    assignment_sent = models.BooleanField(default=False)

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, related_name="events", on_delete=models.CASCADE)

    role_groups: models.ManyToManyField["Event", RoleGroup] = models.ManyToManyField(RoleGroup, blank=True)
    crew = models.ForeignKey(Crew, related_name="events", null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=256)
    slug = models.SlugField()
    banner = models.ImageField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.TextField()

    games: models.Manager["Game"]

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["start_date", "name"]
        constraints = [
                models.UniqueConstraint(fields=["league", "slug"], name="unique_slug_per_league")
                ]

    def days(self) -> list[date]:
        return [
                self.start_date + timedelta(days=i)
                for i in range((self.end_date - self.start_date).days)
        ]

class RoleGroupCrewAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_group = models.ForeignKey(RoleGroup, on_delete=models.CASCADE)
    game: models.ForeignKey['Game'] = models.ForeignKey("Game", related_name="role_group_crew_assignments", on_delete=models.CASCADE)
    crew = models.ForeignKey(Crew, related_name="role_group_assignments", null=True, on_delete=models.SET_NULL)
    crew_overrides = models.ForeignKey(Crew, null=True, on_delete=models.CASCADE)

    # TODO: constrain crew_overrides to have is_override=True
    def effective_crew(self) -> list[CrewAssignment]:
        if not self.crew_overrides: # FIXME: not a good pattern
            self.crew_overrides = Crew(is_override=True, event=self.game.event, role_group=self.role_group)
            self.crew_overrides.save()
            self.save()

        crew_assignments_by_role: dict[uuid.UUID, CrewAssignment] = {}
        if self.crew:
            for assignment in self.crew.assignments.all():
                crew_assignments_by_role[assignment.role.id] = assignment

        for assignment in self.crew_overrides.assignments.all():
            crew_assignments_by_role[assignment.role.id] = assignment

        return list(crew_assignments_by_role.values())

class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, related_name="games", on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    order_key = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    role_groups: models.ManyToManyField[RoleGroup, RoleGroupCrewAssignment] = models.ManyToManyField(RoleGroup, through=RoleGroupCrewAssignment, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "order_key"], name="unique_order_key_event")
        ]
        ordering = [ "order_key" ]

class ApplicationStatus(models.IntegerChoices):
    APPLIED = 1, _("Applied")
    INVITED = 2, _("Invited")
    CONFIRMED = 3, _("Confirmed")
    DECLINED = 4, _("Declined")
    REJECTED = 5, _("Rejected")



class MessageTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, related_name="message_templates", on_delete=models.CASCADE)
    content = models.TextField()

# Application models

class ApplicationKind(models.IntegerChoices):
    CONFIRM_ONLY = 1, _("Confirm Only")
    CONFIRM_THEN_ASSIGN = 2, _("Confirm then Assign")

class ApplicationAvailabilityKind(models.IntegerChoices):
    WHOLE_EVENT = 1, _("Entire Event")
    BY_DAY = 2, _("By Day")
    BY_GAME = 3, _("By Game")

# ApplicationKind and ApplicationAvailabilityKind define the available space
# for event signup types:

# CONFIRM_ONLY is valid with any availability type.
# CONFIRM_THEN_ASSIGN is valid with any availability type.

# BY_GAME requires games and roles to be entered for the application form to be usable;
# the other two do not.

# Single-game events require WHOLE_EVENT (the availability kind isn't meaningful)


class ApplicationFormTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, related_name="application_form_templates", on_delete=models.CASCADE)
    name = models.CharField(max_length=256)

    application_kind = models.IntegerField(choices=ApplicationKind.choices)
    role_groups : models.ManyToManyField["ApplicationFormTemplate", RoleGroup] = models.ManyToManyField(RoleGroup)
    hidden = True
    intro_text = models.TextField()
    requires_profile_fields: models.JSONField[list[str]] = models.JSONField(default=list, blank=True)
    confirmed_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_templates_comfirmed", null=True, blank=True, on_delete=models.SET_NULL)
    assigned_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_templates_assigned", null=True, blank=True, on_delete=models.SET_NULL)
    rejected_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_templates_rejected", null=True, blank=True, on_delete=models.SET_NULL)

class ApplicationForm(models.Model):
    ApplicationAvailabilityKind=ApplicationAvailabilityKind
    ApplicationKind = ApplicationKind

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, related_name="application_forms", on_delete=models.CASCADE)
    slug = models.SlugField()

    application_kind = models.IntegerField(choices=ApplicationKind.choices)
    application_availability_kind = models.IntegerField(choices=ApplicationAvailabilityKind.choices)
    role_groups : models.ManyToManyField["ApplicationForm", RoleGroup] = models.ManyToManyField(RoleGroup)
    hidden = models.BooleanField(default=False)
    intro_text = models.TextField()
    requires_profile_fields : models.JSONField[list[str]] = models.JSONField(default=list, blank=True)
    confirmed_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_confirmed", null=True, blank=True,on_delete=models.SET_NULL)
    assigned_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_assigned",null=True, blank=True,on_delete=models.SET_NULL)
    rejected_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_rejected",null=True, blank=True,on_delete=models.SET_NULL)

    form_questions: models.Manager['Question']
    applications: models.Manager['Application']

    def __str__(self) -> str:
        role_group_names = [rg.name for rg in self.role_groups.all()]
        return f"{self.event.name} ({', '.join(role_group_names)})"

class QuestionKind(models.IntegerChoices):
    SHORT_TEXT = 1, _("Short Text")
    LONG_TEXT = 2, _("Long Text")
    SELECT_ONE = 3, _("Choose One")
    SELECT_MANY = 4, _("Choose Multiple")


class Question(models.Model):
    QuestionKind = QuestionKind
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_form_template = models.ForeignKey(ApplicationFormTemplate, related_name="template_questions", on_delete=models.CASCADE, null=True, blank=True)
    application_form = models.ForeignKey(ApplicationForm, related_name="form_questions", on_delete=models.CASCADE, null=True, blank=True)

    content = models.TextField()
    kind = models.IntegerField(choices=QuestionKind.choices)
    required = models.BooleanField(default=False)
    options: models.JSONField[list[str]] = models.JSONField(default=list, blank=True)
    allow_other = models.BooleanField(default=False)

    # TODO: don't allow an option called "Other" if allow_other is True
    # TODO: require len(options) > 0 if appropriate Kind
    class Meta:
        constraints = [
            models.CheckConstraint(condition = models.Q(application_form_template__isnull=False) ^ models.Q(application_form__isnull=False), name="exactly_one_relation"),
            # TODO models.CheckConstraint(condition = models.Q(allow_other=True) & models.Q(kind__exact=QuestionKind.SELECT_MANY), name="other_only_for_multi")
        ]

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(ApplicationForm, related_name="applications", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="applications",  on_delete=models.CASCADE)
    availability_by_day: models.JSONField[list[str]] = models.JSONField(default=list, blank=True)
    availability_by_game: models.ManyToManyField["Application", Game] = models.ManyToManyField(Game)
    roles: models.ManyToManyField["Application", Role] = models.ManyToManyField(Role)
    status  = models.IntegerField(choices=ApplicationStatus.choices)

    responses: models.Manager["ApplicationResponse"]

    class Meta:
        # TODO: require population of the relevant availability type for the form.
        constraints = [models.UniqueConstraint(fields=["form", "user"], name="one_app_per_event_per_user")]

    def __str__(self) -> str:
        return f"{self.form}: {self.user}"

class ApplicationResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, related_name="responses", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name="responses", on_delete=models.CASCADE)
    content :models.JSONField[str | list[str]]= models.JSONField()


    def __str__(self) -> str:
        return json.dumps(self.content)

    def get_other_response(self) -> str:
        if self.question.kind == QuestionKind.SELECT_MANY and isinstance(self.content, list):
            others = [a for a in self.content if a not in self.question.options]

            if others:
                return others[0]

        return ""
