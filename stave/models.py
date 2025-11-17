import copy
import dataclasses
import enum
import uuid
import zoneinfo
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext_lazy as _

TIMEZONES_CHOICES = [(tz, tz) for tz in sorted(zoneinfo.available_timezones())]


class CertificationLevel(models.TextChoices):
    RECOGNIZED = "Recognized", _("Recognized")
    LEVEL_1 = "Level 1", _("Level 1")
    LEVEL_2 = "Level 2", _("Level 2")
    LEVEL_3 = "Level 3", _("Level 3")


class UserQuerySet(models.QuerySet["User"]):
    def staffed(self, event: "Event") -> "UserQuerySet":
        return self.filter(
            id__in=Application.objects.filter(
                form__event=event, status=ApplicationStatus.ASSIGNED
            ).values("user_id")
        ).distinct()


class User(AbstractBaseUser):
    ALLOWED_PROFILE_FIELDS = [
        "preferred_name",
        "legal_name",
        "pronouns",
        "email",
        "league_affiliation",
        "game_history_url",
        "insurance",
        "nso_certification_level",
        "so_certification_level",
    ]
    USERNAME_FIELD = "id"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    preferred_name = models.CharField(max_length=256, verbose_name=_("derby name"))
    legal_name = models.CharField(max_length=256, blank=True, null=True)
    pronouns = models.CharField(
        max_length=32, blank=True, null=True, verbose_name=_("pronouns")
    )
    email = models.CharField(max_length=256)
    league_affiliation = models.CharField(max_length=256, default=_("Independent"))
    game_history_url = models.URLField(
        verbose_name=_("game history URL"), blank=True, null=True
    )
    insurance = models.CharField(max_length=256, blank=True, null=True)
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
    date_created = models.DateTimeField(auto_now_add=True)

    league_permissions: models.Manager["LeagueUserPermission"]

    objects = UserQuerySet.as_manager()

    # Required to use the Django Admin
    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

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
    event_only = models.BooleanField(default=False)

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
        ordering = ["name"]


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


class LeagueQuerySet(models.QuerySet["League"]):
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
    time_zone = models.CharField(
        max_length=256, choices=TIMEZONES_CHOICES, default="America/Denver"
    )

    events: models.Manager["Event"]
    event_templates: models.Manager["EventTemplate"]
    user_permissions: models.Manager["LeagueUserPermission"]

    objects = LeagueQuerySet.as_manager()

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
            application_form_template.clone_as_template(
                league, message_template_map, event_template_map, role_group_map
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
            game_template.clone_as_template(new_object, role_group_map)

        # Application Form Templates are copied at the League Template level
        # and associated to EventTemplates.

        return new_object

    def clone(self, game_kwargs: list[dict] = None, **kwargs) -> "Event":
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

        game_kwargs = game_kwargs or []
        for i, game_template in enumerate(self.game_templates.all()):
            # GameTemplates do not have required start and end times, but Games do.
            # This is only an issue when we clone non-interactively.
            values = {"event": new_object, "order_key": i + 1}
            if i < len(game_kwargs):
                values.update(game_kwargs[i])
            game_template.clone(**values)

        for application_form_template in self.application_form_templates.all():
            application_form_template.clone(event=new_object)

        return new_object


class GameAssociation(models.TextChoices):
    WFTDA = "WFTDA", _("WFTDA")
    JRDA = "JRDA", _("JRDA")
    MRDA = "MRDA", _("MRDA")
    OTHER = "Other", _("Other")


class GameKind(models.TextChoices):
    CHAMPS = "Champs", _("Champs")
    PLAYOFF = "Playoff", _("Playoff")
    CUPS = "Cups", _("Cups")
    NATIONAL = "National", _("National")
    SANC = "Sanc", _("Sanc")
    REG = "Reg", _("Reg")
    OTHER = "Other", _("Other")


class GameTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_template = models.ForeignKey(
        EventTemplate, related_name="game_templates", on_delete=models.CASCADE
    )
    day = models.IntegerField()
    home_league = models.CharField(max_length=256, null=True, blank=True)
    home_team = models.CharField(max_length=256, null=True, blank=True)
    visiting_league = models.CharField(max_length=256, null=True, blank=True)
    visiting_team = models.CharField(max_length=256, null=True, blank=True)
    association = models.CharField(
        max_length=32, choices=GameAssociation, null=True, blank=True
    )
    kind = models.CharField(max_length=32, choices=GameKind, null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    role_groups: models.ManyToManyField["GameTemplate", RoleGroup] = (
        models.ManyToManyField(RoleGroup, blank=True)
    )
    # TODO: validate that Role Groups have the same League as we do.
    # TODO: validate that Role Groups assigned to us are a strict subset
    # of those assigned to our Event
    # TODO: validate that Role Groups assigned are not event-only

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
        timezone = ZoneInfo(event.league.time_zone)
        values = {
            "event": event,
        }
        if self.start_time:
            values["start_time"] = datetime.combine(
                event.start_date + timedelta(days=self.day - 1),
                self.start_time,
                tzinfo=timezone,
            )
        if self.end_time:
            values["end_time"] = datetime.combine(
                event.start_date + timedelta(days=self.day - 1),
                self.end_time,
                tzinfo=timezone,
            )
        values.update(kwargs)
        new_object = Game.objects.create(**values)

        # Copy Role Group assignments
        for role_group in self.role_groups.filter(event_only=False):
            RoleGroupCrewAssignment.objects.create(
                role_group=role_group, game=new_object
            )

        return new_object


class CrewKind(models.IntegerChoices):
    EVENT_CREW = 1, _("Event Crew")
    GAME_CREW = 2, _("Game Crew")
    OVERRIDE_CREW = 3, _("Override Crew")


class CrewQuerySet(models.QuerySet["Crew"]):
    def prefetch_assignments(self) -> models.QuerySet["Crew"]:
        return self.prefetch_related(
            "assignments",
            "assignments__user",
            "assignments__role",
            "assignments__role__role_group",
        )


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
    objects = CrewQuerySet.as_manager()
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


class EventQuerySet(models.QuerySet["Event"]):
    def visible(self, user: User | AnonymousUser | None) -> models.QuerySet["Event"]:
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
            return self.exclude(
                status=EventStatus.DRAFTING,
            )

    def listed(self, user: User | AnonymousUser | None) -> models.QuerySet["Event"]:
        if isinstance(user, User):
            return (
                self.visible(user)
                .filter(
                    ~Q(status=EventStatus.LINK_ONLY)
                    | Q(
                        league__in=LeagueUserPermission.objects.filter(
                            user=user
                        ).values("league")
                    )
                )
                .exclude(status__in=[EventStatus.CANCELED, EventStatus.COMPLETE])
            )
        else:
            return self.visible(user).exclude(
                status__in=[
                    EventStatus.LINK_ONLY,
                    EventStatus.CANCELED,
                    EventStatus.COMPLETE,
                ]
            )

    def manageable(self, user: User) -> models.QuerySet["Event"]:
        return self.filter(
            league__user_permissions__permission=UserPermission.EVENT_MANAGER,
            league__user_permissions__user=user,
        ).distinct()

    def prefetch_for_display(self) -> models.QuerySet["Event"]:
        return self.select_related("league").prefetch_related("games")


class Event(models.Model):
    EventStatus = EventStatus
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

    objects = EventQuerySet.as_manager()

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
        "Game", related_name="role_group_crew_assignments", on_delete=models.CASCADE
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
        null=True,
    )

    def effective_crew_by_role_id(self) -> dict[uuid.UUID, CrewAssignment]:
        # TODO: ensure these queries are efficient
        crew_assignments_by_role: dict[uuid.UUID, CrewAssignment] = {}

        if self.crew:
            for assignment in self.crew.assignments.all():
                crew_assignments_by_role[assignment.role_id] = assignment
        if self.crew_overrides:
            for assignment in self.crew_overrides.assignments.all():
                crew_assignments_by_role[assignment.role_id] = assignment
        return crew_assignments_by_role

    # TODO: constrain crew_overrides to have is_override=True
    # TODO: constrain crews to match game's Event
    def effective_crew(self) -> list[CrewAssignment]:
        return list(self.effective_crew_by_role_id().values())


class GameQuerySet(models.QuerySet["Game"]):
    def manageable(self, user: User) -> models.QuerySet["Game"]:
        return self.filter(
            event__league__user_permissions__permission=UserPermission.EVENT_MANAGER,
            event__league__user_permissions__user=user,
        ).distinct()


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, related_name="games", on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    home_league = models.CharField(max_length=256)
    home_team = models.CharField(max_length=256)
    visiting_league = models.CharField(max_length=256)
    visiting_team = models.CharField(max_length=256)
    association = models.CharField(max_length=32, choices=GameAssociation)
    kind = models.CharField(max_length=32, choices=GameKind)
    order_key = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    role_groups = models.ManyToManyField(RoleGroup, through=RoleGroupCrewAssignment)

    objects = GameQuerySet.as_manager()

    def get_crew_assignments_by_role_group(
        self,
    ) -> dict[uuid.UUID, RoleGroupCrewAssignment]:
        return {
            rgca.role_group_id: rgca for rgca in self.role_group_crew_assignments.all()
        }

    def __str__(self) -> str:
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "order_key"], name="unique_order_key_event"
            )
        ]
        ordering = ["order_key"]

    def user_by_group_and_role(self, role_group: str, role: str) -> User | None:
        """
        Returns the User for the given role group and role for the game.
        """
        rga = self.role_group_crew_assignments.filter(
            role_group__name=role_group
        ).first()
        if rga:
            for ca in rga.effective_crew():
                if ca.role.name == role:
                    return ca.user
        return None

    def hr(self) -> User | None:
        """
        Returns the Head Referee for the game.
        """
        return self.user_by_group_and_role("SO", "HR")

    def hnso(self) -> User | None:
        """
        Returns the Head NSO for the game.
        """
        return self.user_by_group_and_role("NSO", "HNSO")


class ApplicationStatus(models.IntegerChoices):
    APPLIED = 1, _("Applied")
    INVITATION_PENDING = 7, _("Invitation Pending")
    INVITED = 2, _("Invited")
    CONFIRMED = 3, _("Confirmed")
    DECLINED = 4, _("Declined")
    ASSIGNMENT_PENDING = 10, _("Assignment Pending")
    ASSIGNED = 8, _("Assigned")
    REJECTION_PENDING = 9, _("Rejection Pending")
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
    subject = models.TextField()
    content = models.TextField()
    name = models.CharField(max_length=256)

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
    # With ASSIGN_ONLY, Applications go from Applied
    # to either Assigned, Rejected, or Withdrawn
    # at the point when schedule emails are sent.
    ASSIGN_ONLY = 1, _("Assign Only")
    # With CONFIRM_THEN_ASSIGN, Applications go from
    # Applied to Invited, then to Confirmed or Declined,
    # or to Withdrawn/Rejected.
    CONFIRM_THEN_ASSIGN = 2, _("Confirm then Assign")


class ApplicationAvailabilityKind(models.IntegerChoices):
    WHOLE_EVENT = 1, _("Entire Event")
    BY_DAY = 2, _("By Day")
    BY_GAME = 3, _("By Game")


# ApplicationKind and ApplicationAvailabilityKind define the available space
# for event signup types:

# ASSIGN_ONLY is valid with any availability type.
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

    application_kind = models.IntegerField(
        choices=ApplicationKind.choices, null=False, blank=False
    )
    application_availability_kind = models.IntegerField(
        choices=ApplicationAvailabilityKind.choices, null=False, blank=False
    )
    role_groups: models.ManyToManyField["ApplicationFormTemplate", RoleGroup] = (
        models.ManyToManyField(RoleGroup)
    )
    intro_text = models.TextField(null=True, blank=True)
    requires_profile_fields: models.JSONField[list[str]] = models.JSONField(
        default=list, blank=True
    )
    invitation_email_template = models.ForeignKey(
        MessageTemplate,
        related_name="application_form_templates_invitation",
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
        EventTemplate,
        blank=True,
        related_name="application_form_templates",
        through="ApplicationFormTemplateAssignment",
    )

    def __str__(self):
        return f"{self.name} ({self.league.name if self.league else self.league_template.name})"

    def clone(self, event: Event, **kwargs) -> "ApplicationForm":
        values = {
            "application_kind": self.application_kind,
            "application_availability_kind": self.application_availability_kind,
            "hidden": False,
            "intro_text": self.intro_text,
            "requires_profile_fields": self.requires_profile_fields,
            "invitation_email_template": self.invitation_email_template,
            "schedule_email_template": self.assigned_email_template,
            "rejection_email_template": self.rejected_email_template,
            "event": event,
            "slug": slugify(
                "apply-" + "-".join(sorted(rg.name for rg in self.role_groups.all()))
            ),
        }
        values.update(kwargs)
        new_object = ApplicationForm.objects.create(**values)

        # Assign Role Groups
        new_object.role_groups.set(self.role_groups.all())

        # Questions
        for question in self.template_questions.all():
            new_question = copy.copy(question)
            new_question.id = new_question.pk = None
            new_question._state.adding = True
            new_question.application_form = new_object
            new_question.save()

        return new_object

    def clone_as_template(
        self,
        league: League,
        email_template_map: dict[uuid.UUID, uuid.UUID],
        event_template_map: dict[uuid.UUID, uuid.UUID],
        role_group_map: dict[uuid.UUID, uuid.UUID],
    ) -> "ApplicationFormTemplate":
        new_object = copy.copy(self)
        new_object.id = new_object.pk = None
        new_object._state.adding = True
        new_object.league = league
        new_object.league_template = None

        new_object.invitation_email_template_id = email_template_map[
            new_object.invitation_email_template_id
        ]
        new_object.assigned_email_template_id = email_template_map[
            new_object.assigned_email_template_id
        ]
        new_object.rejected_email_template_id = email_template_map[
            new_object.rejected_email_template_id
        ]

        for question in self.template_questions.all():
            new_question = copy.copy(question)
            new_question.id = new_question.pk = None
            new_question._state.adding = True
            new_question.application_form_template = new_object
            new_question.save()

        new_object.save()
        new_event_template_ids = {
            event_template_map[event_template.id]
            for event_template in self.event_templates.all()
        }
        new_object.event_templates.set(new_event_template_ids)
        new_object.role_groups.set(
            [role_group_map.get(rg.id) for rg in self.role_groups.all()]
        )

        return new_object

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(league__isnull=True) ^ Q(league_template__isnull=True),
                name="either_league_or_league_template_app_form_template",
            )
        ]


class ApplicationFormTemplateAssignment(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event_template", "application_form_template"],
                name="stave_applicationformtemplate_event_templates_applicationformtemplate_id_eventtemplate_id_f2fba8ea_uniq",
            )
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_template = models.ForeignKey(EventTemplate, on_delete=models.DO_NOTHING)
    application_form_template = models.ForeignKey(
        ApplicationFormTemplate, on_delete=models.DO_NOTHING
    )


class ApplicationFormQuerySet(models.QuerySet["ApplicationForm"]):
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
        return (
            self.filter(
                event__status__in=[EventStatus.OPEN, EventStatus.LINK_ONLY],
                event__league__enabled=True,
            ).distinct()
            | self.manageable(user)
        ).exclude(closed=True)

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

    def prefetch_applications(self) -> models.QuerySet["ApplicationForm"]:
        return self.select_related(
            "event",
            "event__league",
        ).prefetch_related(
            "applications",
            "applications__user",
            "applications__roles",
            "applications__roles__role_group",
            "applications__responses",
            "role_groups",
            "role_groups__roles",
            "form_questions",
        )

    def prefetch_crews(self) -> models.QuerySet["ApplicationForm"]:
        return self.select_related("event").prefetch_related(
            "event__crews",
            "event__crews__assignments",
            "event__crews__assignments__user",
        )


class SendEmailContextType(enum.Enum):
    INVITATION = "invitation"
    SCHEDULE = "schedule"
    REJECTION = "rejection"
    CREW = "crew"


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
            "Choose Assign Only to contact applicants only once, when the schedule is finalized. Choose Confirm then Assign to send acceptance messages first, then follow with a schedule."
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
            "You can accept standard fields from the user's profile without requiring them to re-type their information. You always receive the Derby Name field."
        ),
    )
    objects = ApplicationFormQuerySet().as_manager()
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

    @property
    def editable(self) -> bool:
        return not self.applications.exists()

    def event_crews(self) -> models.QuerySet[Crew]:
        return self.event.event_crews().filter(role_group__in=self.role_groups.all())

    def static_crews(self) -> models.QuerySet[Crew]:
        return self.event.static_crews().filter(role_group__in=self.role_groups.all())

    def games(self) -> models.QuerySet[Game]:
        """Return those games from this form's event which have
        at least one of the Role Groups from this form."""
        return self.event.games.filter(
            role_groups__in=self.role_groups.all()
        ).distinct()

    @property
    def role_group_names(self) -> str:
        return ", ".join([rg.name for rg in self.role_groups.all()])

    def __str__(self) -> str:
        return f"{self.event.name} ({self.role_group_names})"

    def save(self, **kwargs):
        if "preferred_name" not in self.requires_profile_fields:
            self.requires_profile_fields.insert(0, "preferred_name")
        super().save(**kwargs)

    def get_absolute_url(self) -> str:
        return reverse(
            "application-form",
            args=[self.event.league.slug, self.event.slug, self.slug],
        )

    def get_edit_url(self) -> str:
        return reverse(
            "form-update",
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

    def get_application_list_url(self) -> str:
        return reverse(
            "form-applications",
            args=[self.event.league.slug, self.event.slug, self.slug],
        )

    def get_comms_center_url(self) -> str:
        return reverse(
            "form-comms", args=[self.event.league.slug, self.event.slug, self.slug]
        )

    def get_staffing_list_url(self) -> str:
        return reverse(
            "event-staff-list", args=[self.event.league.slug, self.event.slug]
        )

    def get_crew_builder_url(self) -> str:
        return reverse(
            "crew-builder", args=[self.event.league.slug, self.event.slug, self.slug]
        )

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
                        status=ApplicationStatus.INVITATION_PENDING
                    ).values("user_id")
                ).distinct()
            case SendEmailContextType.SCHEDULE:
                # A Schedule email goes to any user who's assigned to a crew
                # on our Event where the crew matches one of our Role Groups.

                return User.objects.filter(
                    id__in=self.applications.filter(
                        status=ApplicationStatus.ASSIGNMENT_PENDING
                    ).values("user_id")
                ).distinct()
            case SendEmailContextType.REJECTION:
                return User.objects.filter(
                    id__in=self.applications.filter(
                        status=ApplicationStatus.REJECTION_PENDING
                    ).values("user_id")
                ).distinct()
            case SendEmailContextType.CREW:
                # Staffed users only
                return User.objects.filter(
                    id__in=self.applications.filter(
                        status=ApplicationStatus.ASSIGNED
                    ).values("user_id")
                ).distinct()

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


class ApplicationQuerySet(models.QuerySet["Application"]):
    def visible(self, user: User) -> models.QuerySet["Application"]:
        return self.filter(
            Q(user=user)
            | Q(
                form__event__league__user_permissions__permission=UserPermission.EVENT_MANAGER,
                form__event__league__user_permissions__user=user,
            ),
        ).distinct()

    def prefetch_for_display(self) -> models.QuerySet["Application"]:
        return self.select_related(
            "form", "form__event", "form__event__league"
        ).prefetch_related(
            "form__form_questions",
            "form__role_groups__roles",
            "form__event__games",
            "responses",
            # "availability_by_game",
            "roles",
            "roles__role_group",
        )

    def open(self):
        return self.filter(
            status__in=[
                ApplicationStatus.APPLIED,
            ]
        )

    def in_progress(self):
        return self.filter(
            status__in=[
                ApplicationStatus.ASSIGNMENT_PENDING,
                ApplicationStatus.INVITATION_PENDING,
                ApplicationStatus.INVITED,
                ApplicationStatus.CONFIRMED,
            ]
        )

    def staffed(self):
        return self.filter(status=ApplicationStatus.ASSIGNED)

    def closed(self):
        return self.filter(
            status__in=[
                ApplicationStatus.REJECTED,
                ApplicationStatus.REJECTION_PENDING,
                ApplicationStatus.DECLINED,
                ApplicationStatus.WITHDRAWN,
            ]
        )

    def pending(self):
        return self.filter(
            status__in=[
                ApplicationStatus.INVITATION_PENDING,
                ApplicationStatus.REJECTION_PENDING,
                ApplicationStatus.ASSIGNMENT_PENDING,
            ]
        )


class Application(models.Model):
    ApplicationStatus = ApplicationStatus
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

    @property
    def user_visible_status(self) -> ApplicationStatus:
        match self.status:
            case ApplicationStatus.INVITATION_PENDING:
                return ApplicationStatus.APPLIED
            case ApplicationStatus.REJECTION_PENDING:
                return ApplicationStatus.APPLIED
            case ApplicationStatus.ASSIGNMENT_PENDING:
                if self.form.application_kind == ApplicationKind.CONFIRM_THEN_ASSIGN:
                    return ApplicationStatus.CONFIRMED
                else:
                    return ApplicationStatus.APPLIED
            case _:
                pass

        return ApplicationStatus(self.status)

    responses: models.Manager["ApplicationResponse"]

    objects = ApplicationQuerySet.as_manager()

    class Meta:
        # TODO: require population of the relevant availability type for the form.
        pass

    def __str__(self) -> str:
        return f"{self.form}: {self.user}"

    def get_absolute_url(self) -> str:
        return reverse("view-application", args=[self.id])

    def get_user_data(self) -> dict[str, str]:
        return {
            key: getattr(self.user, key) for key in self.form.requires_profile_fields
        }

    def responses_by_question(self) -> dict[uuid.UUID, "ApplicationResponse"]:
        return {response.question_id: response for response in self.responses.all()}

    def role_names_by_role_group_id(self) -> dict[str, set[str]]:
        names = defaultdict(set)
        for r in self.roles.all():
            names[r.role_group_id].add(r.name)

        return names

    def has_assignments(self) -> bool:
        return CrewAssignment.objects.filter(
            user=self.user, crew__event=self.form.event, role__in=self.roles.all()
        ).exists()

    def save(self, *args, **kwargs):
        if self.status in [
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.REJECTED,
            ApplicationStatus.DECLINED,
        ]:
            # Remove all CrewAssignments for this user that correspond
            # to this application's form's Role Groups.
            CrewAssignment.objects.filter(
                user=self.user,
                crew__event=self.form.event,
                role__role_group__in=self.form.role_groups.all(),
            ).delete()

        return super().save(*args, **kwargs)

    def get_legal_state_changes(self, user: User) -> list[ApplicationStatus]:
        states = list()
        can_manage = (
            Event.objects.manageable(user).filter(id=self.form.event_id).exists()
        )

        if self.form.application_kind == ApplicationKind.CONFIRM_THEN_ASSIGN:
            match self.status:
                case ApplicationStatus.APPLIED:
                    if user == self.user:
                        states.extend(
                            [
                                ApplicationStatus.WITHDRAWN,
                            ]
                        )
                    if can_manage:
                        states.extend(
                            [
                                ApplicationStatus.INVITATION_PENDING,
                                ApplicationStatus.INVITED,
                                ApplicationStatus.REJECTION_PENDING,
                                ApplicationStatus.REJECTED,
                                ApplicationStatus.WITHDRAWN,
                            ]
                        )
                case ApplicationStatus.INVITATION_PENDING:
                    if can_manage:
                        states.extend(
                            [
                                ApplicationStatus.APPLIED,
                                ApplicationStatus.INVITED,
                                ApplicationStatus.CONFIRMED,
                                ApplicationStatus.DECLINED,
                                ApplicationStatus.WITHDRAWN,
                            ]
                        )
                case ApplicationStatus.INVITED:
                    if can_manage or user == self.user:
                        states.extend(
                            [
                                ApplicationStatus.CONFIRMED,
                                ApplicationStatus.DECLINED,
                                ApplicationStatus.WITHDRAWN,
                            ]
                        )
                case ApplicationStatus.DECLINED:
                    pass
                case ApplicationStatus.REJECTION_PENDING:
                    if can_manage:
                        states.extend(
                            [ApplicationStatus.APPLIED, ApplicationStatus.REJECTED]
                        )
                case ApplicationStatus.REJECTED:
                    pass
                case ApplicationStatus.ASSIGNMENT_PENDING:
                    if can_manage:
                        states.extend(
                            [ApplicationStatus.WITHDRAWN, ApplicationStatus.ASSIGNED]
                        )
                    if user == self.user:
                        states.extend(
                            [
                                ApplicationStatus.WITHDRAWN,
                            ]
                        )
                case ApplicationStatus.CONFIRMED | ApplicationStatus.ASSIGNED:
                    if can_manage or user == self.user:
                        states.extend(
                            [
                                ApplicationStatus.WITHDRAWN,
                            ]
                        )
                case ApplicationStatus.WITHDRAWN:
                    pass
        else:
            match self.status:
                case ApplicationStatus.APPLIED:
                    if user == self.user or can_manage:
                        states.extend([ApplicationStatus.WITHDRAWN])
                    if can_manage:
                        states.extend(
                            [
                                ApplicationStatus.REJECTION_PENDING,
                                ApplicationStatus.REJECTED,
                            ]
                        )
                case ApplicationStatus.REJECTION_PENDING:
                    if can_manage:
                        states.extend([ApplicationStatus.APPLIED])
                case ApplicationStatus.ASSIGNMENT_PENDING:
                    if can_manage:
                        states.extend([ApplicationStatus.ASSIGNED])
                case ApplicationStatus.WITHDRAWN:
                    pass
                case _:
                    states.append(ApplicationStatus.WITHDRAWN)

        return states


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
        if isinstance(self.content, list):
            if len(self.content) == 0:
                return ""
            elif len(self.content) == 1:
                return str(self.content[0])
            elif len(self.content) == 2:
                return " and ".join(str(a) for a in self.content)
            else:
                return (
                    ", ".join(str(a) for a in self.content[:-1])
                    + " and "
                    + str(self.content[-1])
                )
        else:
            return self.content

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


class GameHistory:
    game: Game
    user: User
    role: Role
    secondary_role: Role | None

    def __init__(self, game: Game, user: User, role: Role, secondary_role: Role | None):
        self.game = game
        self.user = user
        self.role = role
        self.secondary_role = secondary_role


@dataclasses.dataclass
class MergeField:
    field: str
    description: str


@dataclasses.dataclass
class MergeContext:
    application: Application
    app_form: ApplicationForm
    event: Event
    league: League
    user: User
    sender: User | None

    LEGAL_MERGE_FIELDS = {
        "application": [
            "availability_by_day",
            "availability_by_game",
            "roles",
            "status",
            "link",
        ],
        "app_form": [
            "closed",
            "close_date",
            "hidden",
            "intro_text",
            "link",
            "schedule_link",
        ],
        "event": ["name", "start_date", "end_date", "date_range", "location", "link"],
        "league": ["name", "website", "link"],
        "user": ["preferred_name"],
        "sender": ["preferred_name"],
    }

    def get_merge_fields(self) -> list[MergeField]:
        merge_fields = []
        for entity in self.LEGAL_MERGE_FIELDS:
            for field in self.LEGAL_MERGE_FIELDS[entity]:
                entity_obj = getattr(self, entity)
                if entity_obj:
                    entity_name = entity_obj._meta.verbose_name
                    if field_meta := entity_obj._meta.fields_map.get(field):
                        field_name = field_meta.verbose_name
                    else:
                        # pseudo-fields we provide.
                        field_name = field

                    merge_fields.append(
                        MergeField(
                            f"{{{entity}.{field}}}", f"the {entity_name}'s {field_name}"
                        )
                    )

        return merge_fields

    def get_merge_field_value(self, merge_field: str) -> str | None:
        field_components = merge_field.split(".")
        if len(field_components) != 2:
            return None

        domain = "https://stave.app"  # FIXME: dynamic
        (entity, attr) = field_components
        if (
            entity not in self.LEGAL_MERGE_FIELDS
            or attr not in self.LEGAL_MERGE_FIELDS.get(entity, {})
        ):
            return None

        if attr == "date_range":
            start_date = formats.localize(self.event.start_date, use_l10n=True)
            if self.event.end_date != self.event.start_date:
                end_date = formats.localize(self.event.end_date, use_l10n=True)
                return f"{start_date}–{end_date}"
            else:
                return f"{start_date}"
        elif attr == "link":
            return domain + getattr(self, entity).get_absolute_url()
        elif attr == "schedule_link":
            return domain + reverse(
                "event-user-role-group-schedule",
                args=[
                    self.league.slug,
                    self.event.slug,
                    self.user.id,
                    ",".join(str(rg.id) for rg in self.app_form.role_groups.all()),
                ],
            )
        else:
            entity_obj = getattr(self, entity)
            if entity_obj:
                return str(getattr(entity_obj, attr))
