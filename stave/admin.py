from allauth.account.decorators import secure_admin_login
from django.contrib import admin

from . import models

admin.site.login = secure_admin_login(admin.site.login)


class CrewAssignmentInline(admin.TabularInline):
    model = models.CrewAssignment
    fields = ("event", "role", "user")
    extra = 0


@admin.register(models.Crew)
class CrewAdmin(admin.ModelAdmin):
    inlines = [CrewAssignmentInline]
    list_display = ("event", "role_group", "name", "kind")


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("preferred_name", "email")


class GameTemplateInline(admin.TabularInline):
    model = models.GameTemplate
    fields = ("name",)
    extra = 0


@admin.register(models.EventTemplate)
class EventTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "league", "league_template")
    inlines = [GameTemplateInline]


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
    fields = (
        "order_key",
        "name",
        "home_league",
        "home_team",
        "visiting_league",
        "visiting_team",
        "association",
        "kind",
    )
    extra = 0


class ApplicationFormInline(admin.TabularInline):
    model = models.ApplicationForm
    fields = (
        "slug",
        "hidden",
        "application_kind",
        "application_availability_kind",
    )
    extra = 0


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("league", "start_date", "end_date", "status", "name")
    inlines = [GameInline, ApplicationFormInline]


class LeagueUserPermissionInline(admin.TabularInline):
    model = models.LeagueUserPermission
    fields = ("league", "user", "permission")
    extra = 0


@admin.register(models.League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "enabled")
    inlines = [LeagueUserPermissionInline]


for model in [
    models.Game,
    models.ApplicationForm,
    models.Role,
    models.Question,
    models.RoleGroup,
    models.ApplicationResponse,
    models.CrewAssignment,
    models.GameTemplate,
    models.LeagueTemplate,
]:
    admin.site.register(model)
