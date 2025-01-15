import uuid
from datetime import date, datetime, timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preferred_name = models.CharField(max_length=256)
    pronouns = models.CharField(max_length=32, blank=True, null=True)
    game_history_url = models.URLField(blank=True, null=True)

class RoleStructure(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)

class RoleGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    requires_profile_fields = models.JSONField(default=list, blank=True)

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_group = models.ForeignKey(RoleGroup, related_name="roles", on_delete=models.CASCADE)
    order_key = models.IntegerField()
    name = models.CharField(max_length=256)
    nonexclusive = models.BooleanField(default=False)

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=["role_group", "order_key"], name="unique_order_key")
                ]
        ordering = ["role_group", "order_key"]

class League(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField()
    name = models.CharField(max_length=256)

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
    role_groups = models.ManyToManyField(RoleGroup, blank=True)

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

    role_groups = models.ManyToManyField(RoleGroup, blank=True)

    name = models.CharField(max_length=256)
    banner = models.ImageField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.TextField()

    def days(self) -> list[date]:
        return [
                self.start_date + timedelta(days=i)
                for i in range((self.end_date - self.start_date).days)
        ]


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, related_name="games", on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    order_key = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    role_groups = models.ManyToManyField(RoleGroup, blank=True)

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
    DIRECT_SIGNUP = 3, _("Direct Signup")

class ApplicationAvailabilityKind(models.IntegerChoices):
    WHOLE_EVENT = 1, _("Entire Event")
    BY_DAY = 2, _("By Day")
    BY_GAME = 3, _("By Game")

# ApplicationKind and ApplicationAvailabilityKind define the available space
# for event signup types:

# CONFIRM_ONLY is valid with any availability type.
# CONFIRM_THEN_ASSIGN is valid with any availability type.
# DIRECT_SIGNUP is only valid with BY_GAME and requires games + roles to be present.

# BY_GAME requires games and roles to be entered; the other two do not.

# Single-game events require WHOLE_EVENT (the availability kind isn't meaningful)


class ApplicationFormTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, related_name="application_form_templates", on_delete=models.CASCADE)
    name = models.CharField(max_length=256)

    application_kind = models.IntegerField(choices=ApplicationKind.choices)
    role_groups = models.ManyToManyField(RoleGroup)
    hidden = True
    intro_text = models.TextField()
    requires_profile_fields = models.JSONField(default=list, blank=True)
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
    role_groups = models.ManyToManyField(RoleGroup)
    hidden = models.BooleanField(default=False)
    intro_text = models.TextField()
    requires_profile_fields = models.JSONField(default=list, blank=True)
    confirmed_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_confirmed", null=True, blank=True,on_delete=models.SET_NULL)
    assigned_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_assigned",null=True, blank=True,on_delete=models.SET_NULL)
    rejected_email_template = models.ForeignKey(MessageTemplate, related_name="application_form_rejected",null=True, blank=True,on_delete=models.SET_NULL)


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
    options = models.JSONField(default=list, blank=True)
    allow_other = models.BooleanField(default=False)

    # TODO: don't allow an option called "Other" if allow_other is True
    # TODO: require len(options) > 0 if appropriate Kind
    class Meta:
        constraints = [
            models.CheckConstraint(condition = models.Q(application_form_template__isnull=False) ^ models.Q(application_form__isnull=False), name="exactly_one_relation"),
            # TODO models.CheckConstraint(condition = models.Q(allow_other=True) & ~models.Q(kind__exact=QuestionKind.SELECT_MANY), name="other_only_for_multi")
        ]

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(ApplicationForm, related_name="applications", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="applications",  on_delete=models.CASCADE)
    availability = models.JSONField(default=list, blank=True)
    status = models.IntegerField(choices=ApplicationStatus.choices)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["form", "user"], name="one_app_per_event_per_user")]

class ApplicationResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, related_name="responses", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name="responses", on_delete=models.CASCADE)
    content = models.JSONField()

class RoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, related_name="assignments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="assignments", on_delete=models.CASCADE)
    game = models.ForeignKey(Game, related_name="assignments", on_delete=models.CASCADE, null=True, blank=True)
    status = models.IntegerField(choices=ApplicationStatus.choices)
    application = models.ForeignKey(Application, related_name="assignments", on_delete=models.CASCADE, null=True, blank=True)
