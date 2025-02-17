import uuid
from collections.abc import Iterable
from datetime import timedelta
import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ALLOWED_PROFILE_FIELDS = ["preferred_name", "pronouns", "game_history_url"]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preferred_name = models.CharField(max_length=256, verbose_name=_("preferred name"))
    pronouns = models.CharField(
        max_length=32, blank=True, null=True, verbose_name=_("pronouns")
    )
    game_history_url = models.URLField(
        verbose_name=_("game history URL"), blank=True, null=True
    )
    # TODO: references.
    league_permissions: models.Manager["LeagueUserPermission"]

    def __str__(self) -> str:
        return self.preferred_name


class RoleGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)

    roles: models.Manager["Role"]

    def __str__(self) -> str:
        return self.name


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_group = models.ForeignKey(
        RoleGroup, related_name="roles", on_delete=models.CASCADE
    )
    order_key = models.IntegerField()
    name = models.CharField(max_length=256)
    nonexclusive = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role_group", "order_key"], name="unique_order_key"
            )
        ]
        ordering = ["role_group", "order_key"]


class League(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        help_text=_(
            "The version of the league's name used in web addresses. Should be alphanumeric and contain no spaces, e.g., Central City Derby->central-city-derby"
        )
    )
    name = models.CharField(max_length=256)
    logo = models.ImageField(null=True, blank=True)
    location = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    events: models.Manager["Event"]
    user_permissions: models.Manager["LeagueUserPermission"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("league-detail", args=[self.slug])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["slug"], name="unique_slug")]
        ordering = ["name"]


class UserPermission(models.IntegerChoices):
    LEAGUE_MANAGER = 1, _("League Manager")
    EVENT_MANAGER = 2, _("Event Manager")


class LeagueUserPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, related_name="league_permissions", on_delete=models.CASCADE
    )
    league = models.ForeignKey(
        League, related_name="user_permissions", on_delete=models.CASCADE
    )
    permission = models.IntegerField(choices=UserPermission.choices)


class EventTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    role_groups: models.ManyToManyField["EventTemplate", RoleGroup] = (
        models.ManyToManyField(RoleGroup, blank=True)
    )
    days= models.IntegerField()
    location = models.TextField(blank=True, null=True)


class GameTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_template = models.ForeignKey(EventTemplate, on_delete=models.CASCADE)
    day= models.IntegerField()
    start_time= models.TimeField()
    end_time= models.TimeField()
    role_groups: models.ManyToManyField["GameTemplate", RoleGroup] = models.ManyToManyField(RoleGroup, blank=True)


class Crew(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event: models.ForeignKey["Event"] = models.ForeignKey(
        "Event", related_name="crews", on_delete=models.CASCADE
    )
    role_group = models.ForeignKey(
        RoleGroup, related_name="crews", on_delete=models.CASCADE
    )
    is_override = models.BooleanField(default=False)

    assignments: models.Manager["CrewAssignment"]


class CrewAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crew = models.ForeignKey(Crew, related_name="assignments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="crews", on_delete=models.CASCADE)
    role = models.ForeignKey(
        Role, related_name="crew_assignments", on_delete=models.CASCADE
    )
    assignment_sent = models.BooleanField(default=False)


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, related_name="events", on_delete=models.CASCADE)

    role_groups: models.ManyToManyField["Event", RoleGroup] = models.ManyToManyField(
        RoleGroup, blank=True
    )
    crew = models.ForeignKey(
        Crew, related_name="events", null=True, on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=256)
    slug = models.SlugField()
    banner = models.ImageField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.TextField()

    games: models.Manager["Game"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("event-detail", args=[self.league.slug, self.slug])

    class Meta:
        ordering = ["start_date", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["league", "slug"], name="unique_slug_per_league"
            )
        ]

    def days(self) -> list[str]:
        return [
            str(self.start_date + timedelta(days=i))
            for i in range((self.end_date - self.start_date).days + 1)
        ]


class RoleGroupCrewAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_group = models.ForeignKey(RoleGroup, on_delete=models.CASCADE)
    game: models.ForeignKey["Game"] = models.ForeignKey(
        "Game", related_name="role_groups", on_delete=models.CASCADE
    )
    crew = models.ForeignKey(
        Crew,
        related_name="role_group_assignments",
        null=True,
        on_delete=models.SET_NULL,
    )
    crew_overrides = models.ForeignKey(
        Crew,
        null=True,
        related_name="role_group_override_assignments",
        on_delete=models.CASCADE,
    )

    # TODO: constrain crew_overrides to have is_override=True
    # TODO: constrain crews to match game's Event
    def effective_crew(self) -> list[CrewAssignment]:
        crew_assignments_by_role: dict[uuid.UUID, CrewAssignment] = {}

        if self.crew:
            for assignment in self.crew.assignments.all():
                crew_assignments_by_role[assignment.role.id] = assignment
        if self.crew_overrides:
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

    # TODO: this is a bit weird, how we've set up the through model.
    def assigned_role_groups(self) -> models.QuerySet[RoleGroup]:
        return RoleGroup.objects.filter(rolegroupcrewassignment__in=self.role_groups.all()).distinct()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "order_key"], name="unique_order_key_event"
            )
        ]
        ordering = ["order_key"]


class ApplicationStatus(models.IntegerChoices):
    APPLIED = 1, _("Applied")
    INVITED = 2, _("Invited")
    CONFIRMED = 3, _("Confirmed")
    DECLINED = 4, _("Declined")
    REJECTED = 5, _("Rejected")
    WITHDRAWN = 6, _("Withdrawn")


class MessageTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(
        League, related_name="message_templates", on_delete=models.CASCADE
    )
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
    league = models.ForeignKey(
        League, related_name="application_form_templates", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256)

    application_kind = models.IntegerField(choices=ApplicationKind.choices)
    role_groups: models.ManyToManyField["ApplicationFormTemplate", RoleGroup] = (
        models.ManyToManyField(RoleGroup)
    )
    hidden = True
    intro_text = models.TextField()
    requires_profile_fields: models.JSONField[list[str]] = models.JSONField(
        default=list, blank=True
    )
    confirmed_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_templates_confirmed",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    assigned_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_templates_assigned",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    rejected_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_templates_rejected",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    event_templates: models.ManyToManyField["ApplicationFormTemplate", EventTemplate] = models.ManyToManyField(EventTemplate, blank=True, related_name="application_form_templates")


class ApplicationFormManager(models.Manager["ApplicationForm"]):
    def open(self) -> models.QuerySet["ApplicationForm"]:
        return self.filter(closed=False, hidden=False).order_by(
            "close_date", "event__start_date"
        )  # TODO: make this a CASE()


class ApplicationForm(models.Model):
    ApplicationAvailabilityKind = ApplicationAvailabilityKind
    ApplicationKind = ApplicationKind

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, related_name="application_forms", on_delete=models.CASCADE
    )
    slug = models.SlugField()

    application_kind = models.IntegerField(
        choices=ApplicationKind.choices, null=False, blank=False
    )
    application_availability_kind = models.IntegerField(
        choices=ApplicationAvailabilityKind.choices, null=False, blank=False
    )
    role_groups: models.ManyToManyField["ApplicationForm", RoleGroup] = (
        models.ManyToManyField(RoleGroup)
    )
    closed = models.BooleanField(default=False)
    close_date = models.DateField(null=True, blank=True)
    hidden = models.BooleanField(default=False)
    intro_text = models.TextField()
    requires_profile_fields: models.JSONField[list[str]] = models.JSONField(
        default=list, blank=True
    )
    objects = ApplicationFormManager()
    confirmed_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_confirmed",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    assigned_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_assigned",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    rejected_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_rejected",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    form_questions: models.Manager["Question"]
    applications: models.Manager["Application"]

    def games(self) -> models.QuerySet[Game]:
        """Return those games from this form's event which have
        at least one of the Role Groups from this form."""
        return self.event.games.filter(
            role_groups__role_group__in=self.role_groups.all()
        ).distinct() # TODO: is this correct?

    def __str__(self) -> str:
        role_group_names = [rg.name for rg in self.role_groups.all()]
        return f"{self.event.name} ({', '.join(role_group_names)})"

    def get_absolute_url(self) -> str:
        return reverse(
            "application-form",
            args=[self.event.league.slug, self.event.slug, self.slug],
        )

    # TODO: make it possible to get applications that would otherwise match
    # but are either un-accepted or assigned to other roles.
    def get_applications_for_role(
        self, role: Role, game: Game
    ) -> Iterable["Application"]:
        applications = self.applications.filter(
            roles__name=role.name, roles__role_group_id=role.role_group.id
        )

        # Filter based on our application model.
        if self.application_kind == ApplicationKind.CONFIRM_ONLY:
            applications = applications.filter(
                status__in=[
                    ApplicationStatus.APPLIED,
                    ApplicationStatus.INVITED,
                    ApplicationStatus.CONFIRMED,
                ]
            )
        elif self.application_kind == ApplicationKind.CONFIRM_THEN_ASSIGN:
            applications = applications.filter(status=ApplicationStatus.INVITED)

        # Exclude already-assigned users (to any Role in this Game)
        # TODO: profile this heinous query
        applications = applications.exclude(
            user__in=User.objects.filter(
                crews__role__nonexclusive=False,
                crews__crew__role_group_assignments__game=game,
            )
        )
        applications = applications.exclude(
            user__in=User.objects.filter(
                crews__role__nonexclusive=False,
                crews__crew__role_group_override_assignments__game=game,
            )
        )

        # Predicate for availability.
        if self.application_availability_kind == ApplicationAvailabilityKind.BY_DAY:
            # TODO: can we do this with __contains on Postgres?
            # It's not available on SQLite
            applications = [
                app
                for app in applications
                if str(game.start_time.date()) in app.availability_by_day
            ]

        elif self.application_availability_kind == ApplicationAvailabilityKind.BY_GAME:
            applications = applications.filter(availability_by_game__includes=game)

        return applications

    def get_applications_for_event_role(
        self, role: Role
    ) -> Iterable["Application"]:
        applications = self.applications.filter(
            roles__name=role.name, roles__role_group_id=role.role_group.id
        )

        # Filter based on our application model.
        if self.application_kind == ApplicationKind.CONFIRM_ONLY:
            applications = applications.filter(
                status__in=[
                    ApplicationStatus.APPLIED,
                    ApplicationStatus.INVITED,
                    ApplicationStatus.CONFIRMED,
                ]
            )
        elif self.application_kind == ApplicationKind.CONFIRM_THEN_ASSIGN:
            applications = applications.filter(status=ApplicationStatus.INVITED)

        # Exclude already-assigned users (to any Role in this Event or an individual Game)
        # TODO: profile this heinous query
        applications = applications.exclude(
            user__in=User.objects.filter(
                crews__crew__role_group_assignments__game__event=self.event,
            )
        )
        applications = applications.exclude(
            user__in=User.objects.filter(
                crews__crew__role_group_override_assignments__game__event=self.event,
            )
        )
        applications = applications.exclude(
                user__in=User.objects.filter(
                    crews__role__nonexclusive=False,
                    crews__crew__event=self.event
                )
        )

        # No predicate for availability on event-wide roles.

        return applications

    class Meta:
        ordering = ["slug"]
        constraints = [
            models.UniqueConstraint(
                "slug",
                "event",
                name="no-duplicate-form-slugs",
                violation_error_message=_(
                    "Application form slugs must be unique for any given Event."
                ),
            )
        ]
        # TODO: only one form per Role Group per event


class QuestionKind(models.IntegerChoices):
    SHORT_TEXT = 1, _("Short Text")
    LONG_TEXT = 2, _("Long Text")
    SELECT_ONE = 3, _("Choose One")
    SELECT_MANY = 4, _("Choose Multiple")


class Question(models.Model):
    QuestionKind = QuestionKind
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_form_template = models.ForeignKey(
        ApplicationFormTemplate,
        related_name="template_questions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    application_form = models.ForeignKey(
        ApplicationForm,
        related_name="form_questions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    order_key = models.IntegerField()
    content = models.TextField(verbose_name="title")
    kind = models.IntegerField(choices=QuestionKind.choices)
    required = models.BooleanField(default=False)
    options: models.JSONField[list[str]] = models.JSONField(default=list, blank=True)
    allow_other = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'Question "{self.content}" ({self.kind})'

    # TODO: don't allow an option called "Other" if allow_other is True
    # TODO: require len(options) > 0 if appropriate Kind
    class Meta:
        ordering = ["application_form", "application_form_template", "order_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["application_form", "application_form_template", "order_key"],
                name="unique_question_order_key",
            ),
            models.CheckConstraint(
                condition=models.Q(application_form_template__isnull=False)
                ^ models.Q(application_form__isnull=False),
                name="exactly_one_relation",
            ),
            # TODO models.CheckConstraint(condition = models.Q(allow_other=True) & models.Q(kind__exact=QuestionKind.SELECT_MANY), name="other_only_for_multi")
        ]


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        ApplicationForm, related_name="applications", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="applications", on_delete=models.CASCADE
    )
    availability_by_day: models.JSONField[list[str]] = models.JSONField(
        default=list, blank=True
    )
    availability_by_game: models.ManyToManyField["Application", Game] = (
        models.ManyToManyField(Game)
    )
    roles: models.ManyToManyField["Application", Role] = models.ManyToManyField(Role)
    status = models.IntegerField(choices=ApplicationStatus.choices)

    responses: models.Manager["ApplicationResponse"]

    class Meta:
        # TODO: require population of the relevant availability type for the form.
        # FIXME: this constraint does not appear to work.
        constraints = [
            models.UniqueConstraint(
                fields=["form", "user"], name="one_app_per_event_per_user"
            )
        ]

    def __str__(self) -> str:
        return f"{self.form}: {self.user}"

    def get_user_data(self) -> dict:
        return {
            key: getattr(self.user, key) for key in self.form.requires_profile_fields
        }

    def responses_by_question(self) -> dict[Question, "ApplicationResponse"]:
        return {response.question: response for response in self.responses.all()}

    def role_names(self) -> set[str]:
        return set(r.name for r in self.roles.all())


class ApplicationResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application, related_name="responses", on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question, related_name="responses", on_delete=models.CASCADE
    )
    content: models.JSONField[str | list[str]] = models.JSONField()

    def __str__(self) -> str:
        return json.dumps(self.content)

    def get_other_response(self) -> str:
        if self.question.kind == QuestionKind.SELECT_MANY:
            others = [a for a in self.content if a not in self.question.options]

            if others:
                return others[0]

        return ""

    # TODO: enforce content structure
    class Meta:
        ordering = [
            "question__application_form",
            "question__application_form_template",
            "question__order_key",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "question"],
                name="one_response_per_question_per_application",
            ),
            # models.CheckConstraint(check=Q(application=F("question__application")), name="response_app_and_question_app_match")
        ]
