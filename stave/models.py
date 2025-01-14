import uuid
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
    role_group = models.ForeignKey(RoleGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)

class League(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField()
    name = models.CharField(max_length=256)

    # TODO: slug uniqueness

class LeagueUserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

class EventTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    role_structure = models.ForeignKey(RoleStructure, on_delete=models.PROTECT)

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

    name = models.CharField(max_length=256)
    banner = models.ImageField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.TextField()


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

class EventRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    per_game = models.BooleanField(default=False)

class ApplicationStatus(models.IntegerChoices):
    APPLIED = 1, _("Applied")
    INVITED = 2, _("Invited")
    CONFIRMED = 3, _("Confirmed")
    DECLINED = 4, _("Declined")
    REJECTED = 5, _("Rejected")



class MessageTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    content = models.TextField()

# Application models

class ApplicationKind(models.IntegerChoices):
    CONFIRM_ONLY = 1, _("Confirm Only")
    CONFIRM_THEN_ASSIGN = 2, _("Confirm then Assign")


class ApplicationFormTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    slug = models.SlugField()

    application_kind = models.IntegerField(choices=ApplicationKind.choices)
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
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.IntegerField(choices=ApplicationStatus.choices)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "user"], name="one_app_per_event_per_user")]

class ApplicationResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    content = models.JSONField()

class RoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(EventRole, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    status = models.IntegerField(choices=ApplicationStatus.choices)
    application = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True, blank=True)
