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


for model in [
    models.League,
    models.Event,
    models.Game,
    models.ApplicationForm,
    models.Role,
    models.Question,
    models.RoleGroup,
    models.Application,
    models.ApplicationResponse,
    models.CrewAssignment,
    models.GameTemplate,
    models.LeagueTemplate,
    models.LeagueUserPermission,
]:
    admin.site.register(model)
