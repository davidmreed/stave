from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from stave import models


def create_templates() -> models.LeagueTemplate:
    league_template = models.LeagueTemplate.objects.get_or_create(
        name="Roller Derby League",
        description="Basic setup for a roller derby league, including templates for single and doubleheaders and a multi-day tournament.",
    )[0]
    role_group_nso = models.RoleGroup.objects.get_or_create(
        name="NSO", league_template=league_template
    )[0]
    _role_hnso = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="HNSO", nonexclusive=True, order_key=1
    )[0]
    _role_jt = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="JT", order_key=2
    )[0]
    _role_plt = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PLT", order_key=3
    )[0]
    _role_plt2 = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PLT", order_key=4
    )[0]
    _role_sbo = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="SBO", order_key=5
    )[0]
    _role_sk = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="SK", order_key=6
    )[0]
    _role_sk2 = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="SK", order_key=7
    )[0]
    _role_pbm = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PBM", order_key=8
    )[0]
    _role_pbt = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PBT", order_key=9
    )[0]
    _role_pbt2 = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="PBT", order_key=10
    )[0]
    _role_alt = models.Role.objects.get_or_create(
        role_group=role_group_nso, name="ALT", order_key=11
    )[0]

    role_group_so = models.RoleGroup.objects.get_or_create(
        name="SO", league_template=league_template
    )[0]
    _role_hr = models.Role.objects.get_or_create(
        role_group=role_group_so, name="HR", order_key=1
    )[0]
    _role_ipr = models.Role.objects.get_or_create(
        role_group=role_group_so, name="IPR", order_key=2
    )[0]
    _role_jr = models.Role.objects.get_or_create(
        role_group=role_group_so, name="JR", order_key=3
    )[0]
    _role_jr2 = models.Role.objects.get_or_create(
        role_group=role_group_so, name="JR", order_key=4
    )[0]
    _role_opr = models.Role.objects.get_or_create(
        role_group=role_group_so, name="OPR", order_key=5
    )[0]
    _role_opr2 = models.Role.objects.get_or_create(
        role_group=role_group_so, name="OPR", order_key=6
    )[0]
    _role_opr3 = models.Role.objects.get_or_create(
        role_group=role_group_so, name="OPR", order_key=7
    )[0]
    _role_altref = models.Role.objects.get_or_create(
        role_group=role_group_so, name="ALT", order_key=8
    )[0]

    role_group_tho = models.RoleGroup.objects.get_or_create(
        name="THO", league_template=league_template, event_only=True
    )[0]
    _role_thr = models.Role.objects.get_or_create(
        role_group=role_group_tho, name="THR", order_key=1
    )[0]
    _role_thnso = models.Role.objects.get_or_create(
        role_group=role_group_tho, name="THNSO", order_key=2
    )[0]
    _role_gto = models.Role.objects.get_or_create(
        role_group=role_group_tho, name="GTO", order_key=3
    )[0]

    # Message templates
    # NOTE: changing the text will result in duplication.
    invitation_template = models.MessageTemplate.objects.get_or_create(
        league_template=league_template,
        name=_("Default Invitation Template"),
        subject=_("Invitation to officiate {event.name}"),
        content=_("""Dear {user.preferred_name},

You're invited to officiate [{event.name}]({event.link}), hosted by {league.name}!

{event.name} takes place {event.date_range} at

{event.location}

To accept or decline your invitation, [click here]({application.link}). If you confirm, you'll receive another email when your assignments are finalized.

Thank you!

{sender.preferred_name} and {event.name} organizers"""),
    )[0]
    rejection_template = models.MessageTemplate.objects.get_or_create(
        league_template=league_template,
        name=_("Default Rejection Template"),
        subject=_("Your application to {event.name}"),
        content=_("""Dear {user.preferred_name},

{league.name} wasn't able to accept your application to officiate [{event.name}]({event.link}).

Thank you for your application. Watch [{league.name}]({league.link}) on Stave for more upcoming events.

{sender.preferred_name} and {event.name} organizers"""),
    )[0]
    assignment_template = models.MessageTemplate.objects.get_or_create(
        league_template=league_template,
        name=_("Default Assignment Template"),
        subject=_("Confirmation to officiate {event.name}"),
        content=_("""Dear {user.preferred_name},

You're confirmed to officiate [{event.name}]({event.link}), hosted by {league.name}!

{event.name} takes place {event.date_range} at

{event.location}

Find your [assignments and personalized schedule]({app_form.schedule_link}) on Stave.

Thank you!

{sender.preferred_name} and {event.name} organizers"""),
    )[0]

    # Event templates
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
        event_template=event_template_doubleheader,
        day=1,
    )[0]
    game_template_doubleheader_1.role_groups.set([role_group_so, role_group_nso])
    game_template_doubleheader_2 = models.GameTemplate.objects.exclude(
        id=game_template_doubleheader_1.id
    ).get_or_create(
        event_template=event_template_doubleheader,
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

    # Application form templates
    application_form_template_games, created = (
        models.ApplicationFormTemplate.objects.get_or_create(
            league_template=league_template,
            name="SO and NSO",
            application_kind=models.ApplicationKind.ASSIGN_ONLY,
            application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT,
            intro_text="",
            requires_profile_fields=models.User.ALLOWED_PROFILE_FIELDS,
            invitation_email_template=invitation_template,
            assigned_email_template=assignment_template,
            rejected_email_template=rejection_template,
        )
    )
    if created:
        application_form_template_games.role_groups.set([role_group_nso, role_group_so])
        application_form_template_games.event_templates.set(
            [event_template_single_game]
        )
        application_form_template_games.save()

    application_form_template_doubleheader, created = (
        models.ApplicationFormTemplate.objects.get_or_create(
            league_template=league_template,
            name="SO and NSO",
            application_kind=models.ApplicationKind.ASSIGN_ONLY,
            application_availability_kind=models.ApplicationAvailabilityKind.BY_GAME,
            intro_text="",
            requires_profile_fields=models.User.ALLOWED_PROFILE_FIELDS,
            invitation_email_template=invitation_template,
            assigned_email_template=assignment_template,
            rejected_email_template=rejection_template,
        )
    )
    if created:
        application_form_template_doubleheader.role_groups.set(
            [role_group_nso, role_group_so]
        )
        application_form_template_doubleheader.event_templates.set(
            [event_template_doubleheader]
        )
        application_form_template_doubleheader.save()

    application_form_template_tournament, created = (
        models.ApplicationFormTemplate.objects.get_or_create(
            league_template=league_template,
            name="SO and NSO",
            application_kind=models.ApplicationKind.CONFIRM_THEN_ASSIGN,
            application_availability_kind=models.ApplicationAvailabilityKind.BY_DAY,
            intro_text="",
            requires_profile_fields=models.User.ALLOWED_PROFILE_FIELDS,
            assigned_email_template=assignment_template,
            invitation_email_template=invitation_template,
            rejected_email_template=rejection_template,
        )
    )
    if created:
        application_form_template_tournament.role_groups.set(
            [role_group_nso, role_group_so]
        )
        application_form_template_tournament.event_templates.set(
            [event_template_tournament]
        )
        application_form_template_tournament.save()

    application_form_template_tournament_tho, created = (
        models.ApplicationFormTemplate.objects.get_or_create(
            league_template=league_template,
            name="THO",
            application_kind=models.ApplicationKind.ASSIGN_ONLY,
            application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT,
            intro_text="",
            requires_profile_fields=models.User.ALLOWED_PROFILE_FIELDS,
            assigned_email_template=assignment_template,
            invitation_email_template=invitation_template,
            rejected_email_template=rejection_template,
        )
    )
    if created:
        application_form_template_tournament_tho.role_groups.set([role_group_tho])
        application_form_template_tournament_tho.event_templates.set(
            [event_template_tournament]
        )
        application_form_template_tournament_tho.save()

    return league_template


class Command(BaseCommand):
    help = "Create base templates"

    def handle(self, *_args, **_kwargs):  # type: ignore
        create_templates()
