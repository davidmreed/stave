from django import template
from collections.abc import Mapping, Sequence
from typing import Any, Callable
from .. import models
from stave.templates.stave import contexts

register = template.Library()


class TemplateValidationException(Exception):
    pass


@register.simple_tag(takes_context=True)
def inputs(context: template.Context, model_name: str) -> str:
    # TODO: decide how to dynamic or not this.
    type_ = getattr(contexts, model_name)

    try:
        _ = type_(**(context.dicts[-1]))
    except Exception as e:
        raise TemplateValidationException from e

    return ""


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
