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


for model in [
    models.User,
    models.League,
    models.Event,
    models.Game,
    models.ApplicationForm,
    models.ApplicationFormTemplate,
    models.Role,
    models.Question,
    models.RoleGroup,
    models.Application,
    models.ApplicationResponse,
    models.CrewAssignment,
    models.Message,
    models.MessageTemplate,
    models.LeagueTemplate,
    models.EventTemplate,
    models.LeagueUserPermission,
]:
    admin.site.register(model)
