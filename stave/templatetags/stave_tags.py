from django import template
from collections.abc import Mapping, Sequence
from typing import Any

from .. import models

register = template.Library()


@register.filter
def can_manage_league(user: models.User, league: models.League) -> bool:
    return models.LeagueUserPermission.objects.filter(
        user=user, league=league, permission=models.UserPermission.LEAGUE_MANAGER
    ).exists()


@register.filter
def can_manage_league_events(user: models.User, league: models.League) -> bool:
    return models.LeagueUserPermission.objects.filter(
        user=user, league=league, permission=models.UserPermission.EVENT_MANAGER
    ).exists()


@register.filter
def get(d: Mapping[Any, Any], key: Any) -> Any | None:
    return d.get(key)


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
