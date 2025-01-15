from django.contrib import admin
from allauth.account.decorators import secure_admin_login

from . import models

admin.site.login = secure_admin_login(admin.site.login)

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
        models.RoleAssignment,
    ]:
    admin.site.register(model)
