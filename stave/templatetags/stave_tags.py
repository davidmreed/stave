import copy
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from django import forms, template
from django.db.models import QuerySet
from django.utils.timezone import get_current_timezone

from stave.templates.stave import contexts

from .. import models

register = template.Library()


class TemplateValidationException(Exception):
    pass


@register.filter
def tzname(date: datetime) -> str:
    return get_current_timezone().tzname(date)


@register.filter
def is_form_deleted(form: forms.BaseForm) -> bool:
    return form.data.get(f"{form.prefix}-DELETE") == "on"


@register.simple_tag(takes_context=True)
def inputs(context: template.Context, model_name: str) -> str:
    type_: type = getattr(contexts, model_name)

    input_values = copy.copy(context.dicts[-1])
    if "csrf_token" in input_values:
        del input_values["csrf_token"]

    try:
        _ = type_(**input_values)
    except Exception as e:
        raise TemplateValidationException from e

    return ""


@register.filter
def get_legal_state_changes(
    app: models.Application, user: models.User
) -> list[models.ApplicationStatus]:
    return app.get_legal_state_changes(user)


@register.filter
def is_staffed_on_event(user: models.User, event: models.Event) -> bool:
    if user.is_authenticated:
        return models.User.objects.staffed(event).filter(id=user.id).exists()

    return False


@register.filter
def can_manage_league(user: models.User, league: models.League) -> bool:
    if user.is_authenticated:
        return models.LeagueUserPermission.objects.filter(
            user=user, league=league, permission=models.UserPermission.LEAGUE_MANAGER
        ).exists()
    return False


@register.filter
def can_manage_league_events(user: models.User, league: models.League) -> bool:
    if user.is_authenticated:
        return models.LeagueUserPermission.objects.filter(
            user=user,
            league=league,
            permission=models.UserPermission.EVENT_MANAGER,
        ).exists()
    return False


@register.filter
def can_manage_event(user: models.User, event: models.Event) -> bool:
    if user.is_authenticated:
        return models.LeagueUserPermission.objects.filter(
            user=user,
            league=event.league,
            permission=models.UserPermission.EVENT_MANAGER,
        ).exists()
    return False


@register.filter
def listed_application_forms(
    user: models.User, event: models.Event
) -> QuerySet[models.ApplicationForm]:
    return models.ApplicationForm.objects.listed(user).filter(event=event)


@register.filter
def get(d: Mapping[Any, Any], key: Any) -> Any | None:
    return d.get(key)


@register.filter
def get_profile_field_name(field_name: str) -> str:
    return models.User._meta.get_field(field_name).verbose_name.title()


@register.filter
def commalist(d: Sequence[Any]) -> str:
    if len(d) == 0:
        return ""
    elif len(d) == 1:
        return str(d[0])
    elif len(d) == 2:
        return " and ".join(str(a) for a in d)
    else:
        return ", ".join(str(a) for a in d[:-1]) + " and " + str(d[-1])


@register.filter
def game_history(ca: models.CrewAssignment):
    return models.GameHistory(ca)
