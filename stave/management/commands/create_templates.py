from django.core.management.base import BaseCommand

from stave import models


def create_templates() -> models.LeagueTemplate:
    league_template = models.LeagueTemplate.objects.create(
        name="Roller Derby League",
        description="Basic setup for a roller derby league, including templates for single and doubleheaders and a multi-day tournament",
    )
    role_group_nso = models.RoleGroup.objects.get_or_create(
        name="NSO", league_template=league_template
    )[0]
    role_hnso = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="HNSO", nonexclusive=True, order_key=1
    )[0]
    role_jt = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="JT", order_key=2
    )[0]
    role_plt = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PLT", order_key=3
    )[0]
    role_plt2 = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PLT", order_key=4
    )[0]
    role_sbo = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="SBO", order_key=5
    )[0]
    role_sk = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="SK", order_key=6
    )[0]
    role_sk2 = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="SK", order_key=7
    )[0]
    role_pbm = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PBM", order_key=8
    )[0]
    role_pbt = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PBT", order_key=9
    )[0]
    role_pbt2 = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PBT", order_key=10
    )[0]
    role_alt = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="ALT", order_key=11
    )[0]

    role_group_so = models.RoleGroup.objects.get_or_create(
        name="SO", league_template=league_template
    )[0]
    role_hr = models.Role.objects.get_or_create(
        role_group=role_group_so, name="HR", order_key=1
    )[0]
    role_ipr = models.Role.objects.get_or_create(
        role_group=role_group_so, name="IPR", order_key=2
    )[0]
    role_jr = models.Role.objects.get_or_create(
        role_group=role_group_so, name="JR", order_key=3
    )[0]
    role_jr2 = models.Role.objects.get_or_create(
        role_group=role_group_so, name="JR", order_key=4
    )[0]
    role_opr = models.Role.objects.get_or_create(
        role_group=role_group_so, name="OPR", order_key=5
    )[0]
    role_opr2 = models.Role.objects.get_or_create(
        role_group=role_group_so, name="OPR", order_key=6
    )[0]
    role_opr3 = models.Role.objects.get_or_create(
        role_group=role_group_so, name="OPR", order_key=7
    )[0]
    role_altref = models.Role.objects.get_or_create(
        role_group=role_group_so, name="ALT", order_key=8
    )[0]

    role_group_tho = models.RoleGroup.objects.get_or_create(
        name="THO", league_template=league_template
    )[0]
    role_thr = models.Role.objects.get_or_create(
        role_group=role_group_tho, name="THR", order_key=1
    )[0]
    role_thnso = models.Role.objects.get_or_create(
        role_group=role_group_tho, name="THNSO", order_key=2
    )[0]
    role_gto = models.Role.objects.get_or_create(
        role_group=role_group_tho, name="GTO", order_key=3
    )[0]

    event_template_single_game = models.EventTemplate.objects.get_or_create(
        league_template=league_template,
        name="Singleheader",
        description="A single-game event with SO and NSO roles.",
        days=1,
    )[0]
    event_template_single_game.role_groups.set([role_group_so, role_group_nso])
    game_template_single_game = models.GameTemplate.objects.get_or_create(
        event_template=event_template_single_game,
        day=1,
    )[0]
    game_template_single_game.role_groups.set([role_group_so, role_group_nso])

    event_template_doubleheader = models.EventTemplate.objects.get_or_create(
        league_template=league_template,
        name="Doubleheader",
        description="A single-day, two-game event with SO and NSO roles.",
        days=1,
    )[0]
    event_template_doubleheader.role_groups.set([role_group_so, role_group_nso])
    game_template_doubleheader_1 = models.GameTemplate.objects.get_or_create(
        event_template=event_template_single_game,
        day=1,
    )[0]
    game_template_doubleheader_1.role_groups.set([role_group_so, role_group_nso])
    game_template_doubleheader_2 = models.GameTemplate.objects.get_or_create(
        event_template=event_template_single_game,
        day=1,
    )[0]
    game_template_doubleheader_2.role_groups.set([role_group_so, role_group_nso])

    event_template_tournament = models.EventTemplate.objects.get_or_create(
        league_template=league_template,
        name="Tournament",
        description="A two-day event with THO, SO, and NSO roles.",
        days=2,
    )[0]
    event_template_tournament.role_groups.set(
        [role_group_so, role_group_nso, role_group_tho]
    )

    return league_template


class Command(BaseCommand):
    help = "Create base templates"

    def handle(self, *_args, **_kwargs):  # type: ignore
        _ = create_templates()
