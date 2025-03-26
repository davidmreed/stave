import copy
import enum
import json
import uuid
from collections.abc import Iterable
from datetime import datetime, timedelta

from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class CertificationLevel(models.TextChoices):
    RECOGNIZED = "Recognized", _("Recognized")
    LEVEL_1 = "Level 1", _("Level 1")
    LEVEL_2 = "Level 2", _("Level 2")
    LEVEL_3 = "Level 3", _("Level 3")


# TODO: should this be AbstractBaseUser?
class User(AbstractUser):
    ALLOWED_PROFILE_FIELDS = [
        "preferred_name",
        "legal_name",
        "pronouns",
        "league_affiliation",
        "game_history_url",
        "wftda_insurance_number",
        "nso_certification_level",
        "so_certification_level",
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preferred_name = models.CharField(max_length=256, verbose_name=_("preferred name"))
    legal_name = models.CharField(max_length=256, blank=True, null=True)
    pronouns = models.CharField(
        max_length=32, blank=True, null=True, verbose_name=_("pronouns")
    )
    email = models.CharField(max_length=256)
    league_affiliation = models.CharField(max_length=256, default=_("Independent"))
    game_history_url = models.URLField(
        verbose_name=_("game history URL"), blank=True, null=True
    )
    wftda_insurance_number = models.IntegerField(
        blank=True, null=True, verbose_name=_("WFTDA insurance number")
    )
    nso_certification_level = models.CharField(
        max_length=32,
        choices=CertificationLevel.choices,
        null=True,
        blank=True,
        verbose_name=_("NSO certification level"),
    )
    so_certification_level = models.CharField(
        max_length=32,
        choices=CertificationLevel.choices,
        null=True,
        blank=True,
        verbose_name=_("SO certification level"),
    )

    # TODO: references.
    league_permissions: models.Manager["LeagueUserPermission"]

    def __str__(self) -> str:
        return self.preferred_name


class RoleGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    league = models.ForeignKey(
        "League",
        related_name="role_groups",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    league_template = models.ForeignKey(
        "LeagueTemplate",
        related_name="role_groups",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    roles: models.Manager["Role"]

    def __str__(self) -> str:
        return self.name

    def clone(self, league: "League") -> "RoleGroup":
        new_object = copy.copy(self)
        new_object.id = new_object.pk = None
        new_object._state.adding = True
        new_object.league = league
        new_object.league_template = None
        new_object.save()

        for role in self.roles.all():
            role.clone(new_object)

        return new_object

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(league__isnull=True) ^ Q(league_template__isnull=True),
                name="either_league_or_league_template",
            )
        ]


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

    def clone(self, role_group: RoleGroup) -> "Role":
        new_object = copy.copy(self)
        new_object.id = new_object.pk = None
        new_object._state.adding = True
        new_object.role_group = role_group
        new_object.save()

        return new_object

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role_group", "order_key"], name="unique_order_key"
            )
        ]
        ordering = ["role_group", "order_key"]


class LeagueManager(models.Manager["League"]):
    def visible(self, user: User | AnonymousUser) -> models.QuerySet["League"]:
        if isinstance(user, User):
            return self.filter(
                Q(enabled=True)
                | Q(
                    id__in=LeagueUserPermission.objects.filter(user=user).values(
                        "league_id"
                    )
                )
            )
        else:
            return self.filter(enabled=True)

    def event_manageable(self, user: User) -> models.QuerySet["League"]:
        return self.filter(
            user_permissions__permission=UserPermission.EVENT_MANAGER,
            user_permissions__user=user,
        ).distinct()

    def manageable(self, user: User) -> models.QuerySet["League"]:
        return self.filter(
            user_permissions__permission=UserPermission.LEAGUE_MANAGER,
            user_permissions__user=user,
        ).distinct()


class League(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enabled = models.BooleanField(default=False)
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
    event_templates: models.Manager["EventTemplate"]
    user_permissions: models.Manager["LeagueUserPermission"]

    objects = LeagueManager()

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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "league", "permission"], name="unique_grant"
            )
        ]


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, related_name="subscriptions", on_delete=models.CASCADE
    )
    league = models.ForeignKey(
        League, related_name="subscribers", on_delete=models.CASCADE
    )


class LeagueTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    description = models.TextField()

    role_groups: models.Manager[RoleGroup]
    event_templates: models.Manager["EventTemplate"]
    message_templates: models.Manager["MessageTemplate"]
    application_form_templates: models.Manager["ApplicationFormTemplate"]

    def __str__(self) -> str:
        return self.name

    def clone(self, **kwargs) -> League:
        league = League.objects.create(**kwargs)

        # Copy Role Groups
        role_group_map = {}
        for role_group in self.role_groups.all():
            new_role_group = role_group.clone(league)
            role_group_map[role_group.id] = new_role_group.id

        # Copy Event Templates
        event_template_map = {}
        for event_template in self.event_templates.all():
            new_event_template = event_template.clone_as_template(
                league, role_group_map
            )
            event_template_map[event_template.id] = new_event_template.id

        # Copy Message Templates
        message_template_map = {}
        for message_template in self.message_templates.all():
            new_message_template = message_template.clone_as_template(league)
            message_template_map[message_template.id] = new_message_template.id

        # Copy Application Form Templates
        for application_form_template in self.application_form_templates.all():
            _ = application_form_template.clone_as_template(
                league, event_template_map, message_template_map
            )

        return league


class EventTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_templates",
    )
    league_template = models.ForeignKey(
        LeagueTemplate,
        related_name="event_templates",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=256)
    description = models.TextField()
    role_groups: models.ManyToManyField["EventTemplate", RoleGroup] = (
        models.ManyToManyField(RoleGroup, blank=True)
    )  # TODO: validate that Role Groups are associated to the same
    # League or League Template we are.
    days = models.IntegerField()
    location = models.TextField(blank=True, null=True)

    game_templates: models.Manager["GameTemplate"]

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(league__isnull=True) ^ Q(league_template__isnull=True),
                name="eventtemplate_either_league_or_league_template",
            )
        ]

    def __str__(self) -> str:
        return self.name

    def clone_as_template(
        self, league: League, role_group_map: dict[uuid.UUID, uuid.UUID]
    ) -> "EventTemplate":
        new_object = copy.copy(self)
        new_object.id = new_object.pk = None
        new_object._state.adding = True
        new_object.league = league
        new_object.league_template = None
        new_object.save()

        # Copy Role Group assignments
        new_role_group_ids = {
            role_group_map[role_group.id] for role_group in self.role_groups.all()
        }
        new_object.role_groups.set(new_role_group_ids)

        # Copy Game Templates
        for game_template in self.game_templates.all():
            _ = game_template.clone_as_template(new_object, role_group_map)

        return new_object

    def clone(self, **kwargs) -> "Event":
        values = {
            "league": self.league,
            "location": self.location,
        }
        values.update(kwargs)
        if start_date := values.get("start_date"):
            values["end_date"] = start_date + timedelta(days=self.days - 1)

        new_object = Event.objects.create(
            **values,
        )
        new_object.role_groups.set(self.role_groups.all())

        return new_object


class GameTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_template = models.ForeignKey(
        EventTemplate, related_name="game_templates", on_delete=models.CASCADE
    )
    day = models.IntegerField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    role_groups: models.ManyToManyField["GameTemplate", RoleGroup] = (
        models.ManyToManyField(RoleGroup, blank=True)
    )
    # TODO: validate that Role Groups have the same League as we do.
    # TODO: validate that Role Groups assigned to us are a strict subset
    # of those assigned to our Event

    def clone_as_template(
        self, event_template: EventTemplate, role_group_map: dict[uuid.UUID, uuid.UUID]
    ) -> "GameTemplate":
        new_object = copy.copy(self)
        new_object.id = new_object.pk = None
        new_object._state.adding = True
        new_object.event_template = event_template
        new_object.save()

        # Copy Role Group assignments
        new_role_group_ids = {
            role_group_map[role_group.id] for role_group in self.role_groups.all()
        }
        new_object.role_groups.set(new_role_group_ids)

        return new_object

    def clone(self, event: "Event", **kwargs) -> "Game":
        new_object = Game.objects.create(
            event=event,
            start_time=datetime.combine(
                event.start_date + timedelta(days=self.day - 1), self.start_time
            ),
            end_time=datetime.combine(
                event.start_date + timedelta(days=self.day - 1), self.end_time
            ),
            **kwargs,
        )

        # Copy Role Group assignments
        new_role_group_ids = {
            role_group_map[role_group.id] for role_group in self.role_groups.all()
        }
        new_object.role_groups.set(new_role_group_ids)

        return new_object


class CrewKind(models.IntegerChoices):
    EVENT_CREW = 1, _("Event Crew")
    GAME_CREW = 2, _("Game Crew")
    OVERRIDE_CREW = 3, _("Override Crew")


class Crew(models.Model):
    CrewKind = CrewKind
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    event: models.ForeignKey["Event"] = models.ForeignKey(
        "Event", related_name="crews", on_delete=models.CASCADE
    )
    role_group = models.ForeignKey(
        RoleGroup, related_name="crews", on_delete=models.CASCADE
    )
    # TODO: validate that our Role Group is also assigned to our Event.
    kind = models.IntegerField(
        choices=CrewKind.choices, blank=False, null=False, default=CrewKind.GAME_CREW
    )
    # TODO: validate that this field is consistent with our other data.

    assignments: models.Manager["CrewAssignment"]
    event_role_group_assignments: models.Manager["EventRoleGroupCrewAssignment"]
    role_group_assignments: models.Manager["RoleGroupCrewAssignment"]
    role_group_override_assignments: models.Manager["RoleGroupCrewAssignment"]

    def get_assignments_by_role_id(self) -> dict[uuid.UUID, "CrewAssignment"]:
        return {assignment.role_id: assignment for assignment in self.assignments.all()}

    def get_context(self) -> "None | Game | Event":
        if erga := self.event_role_group_assignments.first():
            return erga.event
        elif rga := self.role_group_assignments.first():
            return rga.game
        elif rgoa := self.role_group_override_assignments.first():
            return rgoa.game

        return None

    def __str__(self) -> str:
        return self.name


class CrewAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crew = models.ForeignKey(Crew, related_name="assignments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="crews", on_delete=models.CASCADE)
    role = models.ForeignKey(
        Role, related_name="crew_assignments", on_delete=models.CASCADE
    )
    # TODO: validate that our Role is a member of the Role Group for our Crew
    assignment_sent = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["crew", "role"], name="one_assignment_per_role"
            ),
            # models.CheckConstraint(condition=Q(role__in=F("crew__role_group__roles")), name="role_must_be_in_crews_rolegroup")
        ]


class EventStatus(models.IntegerChoices):
    DRAFTING = 0, _("Drafting")
    LINK_ONLY = 1, _("Link Only")
    OPEN = 2, _("Open")
    IN_PROGRESS = 3, _("In Progress")
    COMPLETE = 4, _("Complete")
    CANCELED = 5, _("Canceled")


class EventManager(models.Manager["Event"]):
    def visible(self, user: User | AnonymousUser) -> models.QuerySet["Event"]:
        if isinstance(user, User):
            return self.filter(
                ~Q(status=EventStatus.DRAFTING)
                | Q(
                    league__in=LeagueUserPermission.objects.filter(user=user).values(
                        "league"
                    )
                )
            )
        else:
            return self.exclude(status=EventStatus.DRAFTING)

    def listed(self, user: User | AnonymousUser) -> models.QuerySet["Event"]:
        if isinstance(user, User):
            return self.visible(user).filter(
                ~Q(status=EventStatus.LINK_ONLY)
                | Q(
                    league__in=LeagueUserPermission.objects.filter(user=user).values(
                        "league"
                    )
                )
            )
        else:
            return self.visible(user).exclude(status=EventStatus.LINK_ONLY)

    def open(self, user: User | AnonymousUser) -> models.QuerySet["Event"]:
        return self.visible(user).filter(
            status__in=[EventStatus.LINK_ONLY, EventStatus.OPEN]
        )

    def manageable(self, user: User) -> models.QuerySet["Event"]:
        return self.filter(
            league__user_permissions__permission=UserPermission.EVENT_MANAGER,
            league__user_permissions__user=user,
        ).distinct()


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    league = models.ForeignKey(League, related_name="events", on_delete=models.CASCADE)
    status = models.IntegerField(
        choices=EventStatus.choices, default=EventStatus.DRAFTING
    )

    role_groups: models.ManyToManyField["Event", RoleGroup] = models.ManyToManyField(
        RoleGroup, blank=True
    )
    # TODO: validate that our Role Groups are assigned to our League
    name = models.CharField(max_length=256)
    slug = models.SlugField(
        help_text=_(
            "The version of the event's name used in web addresses. Should be alphanumeric and contain no spaces, e.g., Summer Throwdown->summer-throwdown"
        )
    )
    banner = models.ImageField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.TextField()

    games: models.Manager["Game"]

    objects = EventManager()

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

    def event_crews(self) -> models.QuerySet[Crew]:
        return self.crews.filter(kind=CrewKind.EVENT_CREW)

    def static_crews(self) -> models.QuerySet[Crew]:
        return self.crews.filter(kind=CrewKind.GAME_CREW)


class EventRoleGroupCrewAssignment(models.Model):
    event = models.ForeignKey(
        Event, related_name="role_group_crew_assignments", on_delete=models.CASCADE
    )
    role_group = models.ForeignKey(
        RoleGroup, related_name="event_crew_assignments", on_delete=models.CASCADE
    )
    crew = models.ForeignKey(
        Crew, related_name="event_role_group_assignments", on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        if not self.crew_id:
            self.crew_id = Crew.objects.create(
                name=f"{self.role_group} Crew",
                event=self.event,
                kind=CrewKind.EVENT_CREW,
                role_group=self.role_group,
            ).id

        return super().save(*args, **kwargs)

    class Meta:  # TODO: enforce validation
        constraints = [
            # models.CheckConstraint(condition=Q(crew__event=F("event")), name="crew_must_match_event"),
            # models.CheckConstraint(condition=Q(role_group__in=F("event__role_groups")), name="role_group_must_be_assigned_to_event")
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
        editable=False,
        related_name="role_group_override_assignments",
        on_delete=models.CASCADE,
    )

    def save(self, *args, **kwargs):
        if not self.crew_overrides_id:
            self.crew_overrides_id = Crew.objects.create(
                kind=CrewKind.OVERRIDE_CREW,
                role_group=self.role_group,
                event=self.game.event,
            ).id

        return super().save(*args, **kwargs)

    def effective_crew_by_role_id(self) -> dict[uuid.UUID, CrewAssignment]:
        crew_assignments_by_role: dict[uuid.UUID, CrewAssignment] = {}

        if self.crew:
            for assignment in self.crew.assignments.all():
                crew_assignments_by_role[assignment.role.id] = assignment
        if self.crew_overrides:
            for assignment in self.crew_overrides.assignments.all():
                crew_assignments_by_role[assignment.role.id] = assignment
        return crew_assignments_by_role

    # TODO: constrain crew_overrides to have is_override=True
    # TODO: constrain crews to match game's Event
    def effective_crew(self) -> list[CrewAssignment]:
        return list(self.effective_crew_by_role_id().values())


class GameManager(models.Manager["Game"]):
    def manageable(self, user: User) -> models.QuerySet["Game"]:
        return self.filter(
            event__league__user_permissions__permission=UserPermission.LEAGUE_MANAGER,
            event__league__user_permissions__user=user,
        ).distinct()


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, related_name="games", on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    order_key = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    objects = GameManager()

    def get_crew_assignments_by_role_group(
        self,
    ) -> dict[uuid.UUID, RoleGroupCrewAssignment]:
        return {rgca.role_group_id: rgca for rgca in self.role_groups.all()}

    def __str__(self) -> str:
        return self.name

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
        League,
        related_name="message_templates",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    league_template = models.ForeignKey(
        LeagueTemplate,
        related_name="message_templates",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    content = models.TextField()

    def clone_as_template(self, league: League) -> "MessageTemplate":
        new_object = copy.copy(self)
        new_object.id = new_object.pk = None
        new_object._state.adding = True
        new_object.league = league
        new_object.league_template = None
        new_object.save()

        return new_object

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(league__isnull=True) ^ Q(league_template__isnull=True),
                name="messagetemplate_either_league_or_league_template",
            )
        ]


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=256)
    content_plain_text = models.TextField()
    content_html = models.TextField()
    user = models.ForeignKey(User, related_name="messages", on_delete=models.CASCADE)
    sent = models.BooleanField(default=False)
    sent_date = models.DateTimeField(null=True)
    tries = models.IntegerField(default=0)


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
        League,
        related_name="application_form_templates",
        on_delete=models.CASCADE,
        null=True,
    )
    league_template = models.ForeignKey(
        LeagueTemplate,
        related_name="application_form_templates",
        on_delete=models.CASCADE,
        null=True,
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

    event_templates: models.ManyToManyField[
        "ApplicationFormTemplate", EventTemplate
    ] = models.ManyToManyField(
        EventTemplate, blank=True, related_name="application_form_templates"
    )

    def clone(self, event: Event, **kwargs) -> "ApplicationForm":
        values = {
            "league": self.league,
            "application_kind": self.application_kind,  # TODO: app availability kind?
            "hidden": self.hidden,
            "intro_text": self.intro_text,
            "requires_profile_fields": self.requires_profile_fields,
            "confirmed_email_template": self.confirmed_email_template,
            "assigned_email_template": self.assigned_email_template,
            "rejected_email_template": self.rejected_email_template,
            "event": event,
        }
        values.update(kwargs)
        new_object = ApplicationForm.objects.create(**values)

        # Assign Role Groups
        new_object.role_groups.set(self.role_groups.all())

        return new_object

    def clone_as_template(
        self,
        league: League,
        email_template_map: dict[uuid.UUID, uuid.UUID],
        event_template_map: dict[uuid.UUID, uuid.UUID],
    ) -> "ApplicationFormTemplate":
        new_object = copy.copy(self)
        new_object.id = new_object.pk = None
        new_object._state.adding = True
        new_object.league = league
        new_object.league_template = None

        new_object.confirmed_email_template_id = email_template_map[
            new_object.confirmed_email_template_id
        ]
        new_object.assigned_email_template_id = email_template_map[
            new_object.assigned_email_template_id
        ]
        new_object.rejected_email_template_id = email_template_map[
            new_object.rejected_email_template_id
        ]

        for question in self.form_questions.all():
            new_question = copy.copy(question)
            new_question.id = new_object.pk = None
            new_question._state.adding = True
            new_question.application_form_template = new_object
            new_question.save()

        new_object.save()
        new_event_template_ids = {
            event_template_map[event_template.id]
            for event_template in self.event_templates.all()
        }
        new_object.event_templates.set(new_event_template_ids)

        return new_object

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(league__isnull=True) ^ Q(league_template__isnull=True),
                name="either_league_or_league_template_app_form_template",
            )
        ]


class ApplicationFormManager(models.Manager["ApplicationForm"]):
    def listed(self, user: User | AnonymousUser) -> models.QuerySet["ApplicationForm"]:
        """ApplicationForms that are listed on the homepage and other timelines"""
        return (
            self.manageable(user)
            | self.filter(
                closed=False,
                hidden=False,
                event__status=EventStatus.OPEN,
                event__league__enabled=True,
            ).distinct()
        ).order_by("close_date", "event__start_date")  # TODO: make this a CASE()

    def accessible(
        self, user: User | AnonymousUser
    ) -> models.QuerySet["ApplicationForm"]:
        """ApplicationForms that can be accessed by a user who knows the URL"""
        return self.filter(
            event__league__enabled=True,
        ).exclude(event__status=EventStatus.DRAFTING).distinct() | self.manageable(user)

    def submittable(
        self, user: User | AnonymousUser
    ) -> models.QuerySet["ApplicationForm"]:
        return self.filter(
            closed=False,
            event__status__in=[EventStatus.OPEN, EventStatus.LINK_ONLY],
            event__league__enabled=True,
        ).distinct() | self.manageable(user)

    def manageable(
        self, user: User | AnonymousUser
    ) -> models.QuerySet["ApplicationForm"]:
        if isinstance(user, AnonymousUser):
            return self.none()
        else:
            return (
                self.filter(
                    event__league__user_permissions__permission=UserPermission.EVENT_MANAGER,
                    event__league__user_permissions__user=user,
                )
                .distinct()
                .exclude(event__status__in=[EventStatus.CANCELED, EventStatus.COMPLETE])
            )


class SendEmailContextType(enum.Enum):
    INVITATION = "invitation"
    SCHEDULE = "schedule"
    REJECTION = "rejection"


class ApplicationForm(models.Model):
    ApplicationAvailabilityKind = ApplicationAvailabilityKind
    ApplicationKind = ApplicationKind

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, related_name="application_forms", on_delete=models.CASCADE
    )
    slug = models.SlugField(
        help_text=_(
            "Form name used in web addresses. Should be alphanumeric and contain no spaces, e.g., apply or apply-nso"
        )
    )

    application_kind = models.IntegerField(
        choices=ApplicationKind.choices,
        null=False,
        blank=False,
        verbose_name=_("application process"),
        help_text=_(
            "Choose Confirm Only to contact applicants only once, when the schedule is finalized. Choose Confirm then Assign to send acceptance messages first, then follow with a schedule."
        ),
    )
    application_availability_kind = models.IntegerField(
        choices=ApplicationAvailabilityKind.choices,
        null=False,
        blank=False,
        verbose_name=_("availability type"),
        help_text=_(
            "You can request availability at the level of the whole event, whole days, or by individual game. Single-game events must use Entire Event."
        ),
    )
    role_groups: models.ManyToManyField["ApplicationForm", RoleGroup] = (
        models.ManyToManyField(
            RoleGroup,
            help_text=_(
                "The role groups covered by this form. You can select any or all of the role groups assigned to the event. Each role group can appear on only one form."
            ),
        )
    )
    closed = models.BooleanField(default=False)
    close_date = models.DateField(null=True, blank=True)
    hidden = models.BooleanField(
        default=False,
        help_text=_(
            "Hidden forms are accessible only by direct link, and aren't listed on Stave."
        ),
    )
    intro_text = models.TextField(
        help_text=_(
            "Introduce the event to your applicants. You don't need to include dates or locations, because these are recorded on the event already. You can use Markdown to format this text."
        )
    )
    requires_profile_fields: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text=_(
            "You can accept standard fields from the user's profile without requiring them to re-type their information."
        ),
    )
    objects = ApplicationFormManager()
    invitation_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_invitation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    schedule_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_schedule",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    rejection_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_rejection",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    form_questions: models.Manager["Question"]
    applications: models.Manager["Application"]

    def event_crews(self) -> models.QuerySet[Crew]:
        return self.event.event_crews().filter(role_group__in=self.role_groups.all())

    def static_crews(self) -> models.QuerySet[Crew]:
        return self.event.static_crews().filter(role_group__in=self.role_groups.all())

    def games(self) -> models.QuerySet[Game]:
        """Return those games from this form's event which have
        at least one of the Role Groups from this form."""
        return self.event.games.filter(
            role_groups__role_group__in=self.role_groups.all()
        ).distinct()  # TODO: is this correct?

    def __str__(self) -> str:
        role_group_names = [rg.name for rg in self.role_groups.all()]
        return f"{self.event.name} ({', '.join(role_group_names)})"

    def get_absolute_url(self) -> str:
        return reverse(
            "application-form",
            args=[self.event.league.slug, self.event.slug, self.slug],
        )

    def get_schedule_url(self) -> str | None:
        if self.role_groups.all():
            return reverse(
                "event-role-group-schedule",
                args=[
                    self.event.league.slug,
                    self.event.slug,
                    ",".join(str(rg.id) for rg in self.role_groups.all()),
                ],
            )

    def get_crew_builder_url(self) -> str:
        return reverse(
            "crew-builder", args=[self.event.league.slug, self.event.slug, self.slug]
        )

    # TODO: make it possible to get applications that would otherwise match
    # but are either un-accepted or assigned to other roles.
    # TODO: handle games with overlapping times.
    def get_applications_for_role(
        self, role: Role, context: Game | Event | None
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

        # Exclude already-assigned users based on our given context.
        # If the context is a Game, exclude users already assigned to that Game
        # If the context is an Event, exclude users already assigned an Event-level role.
        # If the context is None, we're building a static crew, so we exclude users
        # who are already assigned to any crew type on this event.

        if isinstance(context, Game):
            # TODO: profile this heinous query
            applications = applications.exclude(
                user__in=User.objects.filter(
                    crews__role__nonexclusive=False,
                    crews__crew__role_group_assignments__game=context,
                )
            )
            applications = applications.exclude(
                user__in=User.objects.filter(
                    crews__role__nonexclusive=False,
                    crews__crew__role_group_override_assignments__game=context,
                )
            )
        elif isinstance(context, Event):
            applications = applications.exclude(
                user__in=User.objects.filter(
                    crews__crew__event_role_groups__event=context
                )
            )
        elif context is None:
            applications = applications.exclude(
                user__in=User.objects.filter(crews__crew__event=self.event)
            )

        # Predicate for availability.
        # TODO: figure out what this looks like for other contexts
        if isinstance(context, Game):
            if self.application_availability_kind == ApplicationAvailabilityKind.BY_DAY:
                # TODO: can we do this with __contains on Postgres?
                # It's not available on SQLite
                applications = [
                    app
                    for app in applications
                    if str(context.start_time.date()) in app.availability_by_day
                ]

            elif (
                self.application_availability_kind
                == ApplicationAvailabilityKind.BY_GAME
            ):
                applications = applications.filter(availability_by_game=context)

        return applications

    def get_template_for_context_type(
        self, context: SendEmailContextType
    ) -> MessageTemplate | None:
        match context:
            case SendEmailContextType.INVITATION:
                return self.invitation_email_template
            case SendEmailContextType.SCHEDULE:
                return self.schedule_email_template
            case SendEmailContextType.REJECTION:
                return self.rejection_email_template

    def get_user_queryset_for_context_type(
        self, context: SendEmailContextType
    ) -> models.QuerySet[User]:
        match context:
            case SendEmailContextType.INVITATION:
                return User.objects.filter(
                    id__in=self.applications.filter(
                        status=ApplicationStatus.INVITED, invitation_email_sent=False
                    ).values("user_id")
                )
            case SendEmailContextType.SCHEDULE:
                # A Schedule email goes to any user who's assigned to a crew
                # on our Event where the crew matches one of our Role Groups.
                return User.objects.filter()
                # TODO
            case SendEmailContextType.REJECTION:
                return User.objects.filter(
                    id__in=self.applications.filter(
                        status=ApplicationStatus.REJECTED, rejection_email_sent=False
                    ).values("user_id")
                )

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
        # TODO: clamp AvailabilityKind for event-wide Role Groups


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


class ApplicationManager(models.Manager["Application"]):
    def visible(self, user: User) -> models.QuerySet["Application"]:
        return self.filter(
            Q(user=user)
            | Q(
                form__event__league__user_permissions__permission=UserPermission.EVENT_MANAGER,
                form__event__league__user_permissions__user=user,
            ),
        ).distinct()


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
    invitation_email_sent = models.BooleanField(default=False)
    decline_email_set = models.BooleanField(default=False)
    schedule_email_sent = models.BooleanField(default=False)

    responses: models.Manager["ApplicationResponse"]

    objects = ApplicationManager()

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

    def get_absolute_url(self) -> str:
        return reverse("view-application", args=[self.id])

    def get_user_data(self) -> dict[str, str]:
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
