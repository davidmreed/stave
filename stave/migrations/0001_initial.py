# Generated by Django 5.1.4 on 2025-02-01 01:43

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Crew",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("is_override", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("order_key", models.IntegerField()),
                ("name", models.CharField(max_length=256)),
                ("nonexclusive", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["role_group", "order_key"],
            },
        ),
        migrations.CreateModel(
            name="RoleGroup",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                ("requires_profile_fields", models.JSONField(blank=True, default=list)),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("preferred_name", models.CharField(max_length=256)),
                ("pronouns", models.CharField(blank=True, max_length=32, null=True)),
                ("game_history_url", models.URLField(blank=True, null=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                ("slug", models.SlugField()),
                ("banner", models.ImageField(blank=True, null=True, upload_to="")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("location", models.TextField()),
                (
                    "crew",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="events",
                        to="stave.crew",
                    ),
                ),
            ],
            options={
                "ordering": ["start_date", "name"],
            },
        ),
        migrations.AddField(
            model_name="crew",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="crews",
                to="stave.event",
            ),
        ),
        migrations.CreateModel(
            name="ApplicationForm",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("slug", models.SlugField()),
                (
                    "application_kind",
                    models.IntegerField(
                        choices=[
                            (1, "Confirm Only"),
                            (2, "Confirm then Assign"),
                            (3, "Direct Signup"),
                        ]
                    ),
                ),
                (
                    "application_availability_kind",
                    models.IntegerField(
                        choices=[(1, "Entire Event"), (2, "By Day"), (3, "By Game")]
                    ),
                ),
                ("hidden", models.BooleanField(default=False)),
                ("intro_text", models.TextField()),
                ("requires_profile_fields", models.JSONField(blank=True, default=list)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="application_forms",
                        to="stave.event",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Game",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                ("order_key", models.IntegerField()),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="games",
                        to="stave.event",
                    ),
                ),
            ],
            options={
                "ordering": ["order_key"],
            },
        ),
        migrations.CreateModel(
            name="Application",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("availability_by_day", models.JSONField(blank=True, default=list)),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (1, "Applied"),
                            (2, "Invited"),
                            (3, "Confirmed"),
                            (4, "Declined"),
                            (5, "Rejected"),
                        ]
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "form",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to="stave.applicationform",
                    ),
                ),
                ("availability_by_game", models.ManyToManyField(to="stave.game")),
                ("roles", models.ManyToManyField(to="stave.role")),
            ],
        ),
        migrations.CreateModel(
            name="League",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("slug", models.SlugField()),
                ("name", models.CharField(max_length=256)),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.UniqueConstraint(fields=("slug",), name="unique_slug")
                ],
            },
        ),
        migrations.AddField(
            model_name="event",
            name="league",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to="stave.league",
            ),
        ),
        migrations.CreateModel(
            name="LeagueUserRole",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "league",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="stave.league"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MessageTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("content", models.TextField()),
                (
                    "league",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="message_templates",
                        to="stave.league",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ApplicationFormTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                (
                    "application_kind",
                    models.IntegerField(
                        choices=[
                            (1, "Confirm Only"),
                            (2, "Confirm then Assign"),
                            (3, "Direct Signup"),
                        ]
                    ),
                ),
                ("intro_text", models.TextField()),
                ("requires_profile_fields", models.JSONField(blank=True, default=list)),
                (
                    "league",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="application_form_templates",
                        to="stave.league",
                    ),
                ),
                (
                    "assigned_email_template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="application_form_templates_assigned",
                        to="stave.messagetemplate",
                    ),
                ),
                (
                    "confirmed_email_template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="application_form_templates_comfirmed",
                        to="stave.messagetemplate",
                    ),
                ),
                (
                    "rejected_email_template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="application_form_templates_rejected",
                        to="stave.messagetemplate",
                    ),
                ),
                ("role_groups", models.ManyToManyField(to="stave.rolegroup")),
            ],
        ),
        migrations.AddField(
            model_name="applicationform",
            name="assigned_email_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="application_form_assigned",
                to="stave.messagetemplate",
            ),
        ),
        migrations.AddField(
            model_name="applicationform",
            name="confirmed_email_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="application_form_confirmed",
                to="stave.messagetemplate",
            ),
        ),
        migrations.AddField(
            model_name="applicationform",
            name="rejected_email_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="application_form_rejected",
                to="stave.messagetemplate",
            ),
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("content", models.TextField()),
                (
                    "kind",
                    models.IntegerField(
                        choices=[
                            (1, "Short Text"),
                            (2, "Long Text"),
                            (3, "Choose One"),
                            (4, "Choose Multiple"),
                        ]
                    ),
                ),
                ("required", models.BooleanField(default=False)),
                ("options", models.JSONField(blank=True, default=list)),
                ("allow_other", models.BooleanField(default=False)),
                (
                    "application_form",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="form_questions",
                        to="stave.applicationform",
                    ),
                ),
                (
                    "application_form_template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="template_questions",
                        to="stave.applicationformtemplate",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ApplicationResponse",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("content", models.JSONField()),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="stave.application",
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="responses",
                        to="stave.question",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CrewAssignment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("assignment_sent", models.BooleanField(default=False)),
                (
                    "crew",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="stave.crew",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="crews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="crew_assignments",
                        to="stave.role",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="role",
            name="role_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="roles",
                to="stave.rolegroup",
            ),
        ),
        migrations.CreateModel(
            name="EventTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                (
                    "league",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="stave.league"
                    ),
                ),
                (
                    "role_groups",
                    models.ManyToManyField(blank=True, to="stave.rolegroup"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="event",
            name="role_groups",
            field=models.ManyToManyField(blank=True, to="stave.rolegroup"),
        ),
        migrations.AddField(
            model_name="crew",
            name="role_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="crews",
                to="stave.rolegroup",
            ),
        ),
        migrations.AddField(
            model_name="applicationform",
            name="role_groups",
            field=models.ManyToManyField(to="stave.rolegroup"),
        ),
        migrations.CreateModel(
            name="RoleGroupCrewAssignment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "crew",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_group_assignments",
                        to="stave.crew",
                    ),
                ),
                (
                    "crew_overrides",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stave.crew",
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_group_crew_assignments",
                        to="stave.game",
                    ),
                ),
                (
                    "role_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stave.rolegroup",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="game",
            name="role_groups",
            field=models.ManyToManyField(
                blank=True,
                through="stave.RoleGroupCrewAssignment",
                to="stave.rolegroup",
            ),
        ),
        migrations.AddConstraint(
            model_name="question",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("application_form_template__isnull", False),
                    ("application_form__isnull", False),
                    _connector="XOR",
                ),
                name="exactly_one_relation",
            ),
        ),
        migrations.AddConstraint(
            model_name="application",
            constraint=models.UniqueConstraint(
                fields=("form", "user"), name="one_app_per_event_per_user"
            ),
        ),
        migrations.AddConstraint(
            model_name="role",
            constraint=models.UniqueConstraint(
                fields=("role_group", "order_key"), name="unique_order_key"
            ),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.UniqueConstraint(
                fields=("league", "slug"), name="unique_slug_per_league"
            ),
        ),
        migrations.AddConstraint(
            model_name="game",
            constraint=models.UniqueConstraint(
                fields=("event", "order_key"), name="unique_order_key_event"
            ),
        ),
    ]
