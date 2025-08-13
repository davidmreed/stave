from allauth.account.decorators import secure_admin_login
from django.contrib import admin

from . import models

admin.site.login = secure_admin_login(admin.site.login)


class CrewAssignmentInline(admin.TabularInline):
    model = models.CrewAssignment
    list_display = ("event", "role", "user")


@admin.register(models.Crew)
class CrewAdmin(admin.ModelAdmin):
    inlines = [CrewAssignmentInline]
    list_display = ("event", "role_group", "name", "kind")


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("preferred_name", "email")


class ApplicationFormTemplateInline(admin.TabularInline):
    model = models.EventTemplate.application_form_templates.through
    list_display = ("name",)


class GameTemplateInline(admin.TabularInline):
    model = models.GameTemplate
    list_display = ("name",)


@admin.register(models.EventTemplate)
class EventTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "league", "league_template")
    inlines = [GameTemplateInline, ApplicationFormTemplateInline]


@admin.register(models.ApplicationFormTemplate)
class ApplicationFormTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "league", "league_template")


@admin.register(models.MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "league", "league_template", "subject")


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sent_date", "sent", "user", "subject")


class ApplicationResponseInline(admin.TabularInline):
    model = models.ApplicationResponse
    list_display = ("question", "content")


@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "form", "form__event", "status")
    inlines = [ApplicationResponseInline]


class GameInline(admin.TabularInline):
    model = models.Game
    list_display = (
        "order_key",
        "name",
        "home_league",
        "home_team",
        "visiting_league",
        "visiting_team",
        "association",
        "kind",
    )


class ApplicationFormInline(admin.TabularInline):
    model = models.ApplicationForm
    list_display = (
        "slug",
        "hidden",
        "application_kind",
        "application_availability_kind",
    )


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("league", "start_date", "end_date", "status", "name")
    inlines = [GameInline, ApplicationFormInline]


for model in [
    models.League,
    models.Game,
    models.ApplicationForm,
    models.Role,
    models.Question,
    models.RoleGroup,
    models.ApplicationResponse,
    models.CrewAssignment,
    models.GameTemplate,
    models.LeagueTemplate,
    models.LeagueUserPermission,
]:
    admin.site.register(model)
