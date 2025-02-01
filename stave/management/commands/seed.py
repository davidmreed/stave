from django.core.management.base import BaseCommand
from stave import models
from datetime import datetime, date, time

class Command(BaseCommand):
    help = "seed database for testing and development."

    def handle(self, *_args, **_kwargs): # type: ignore
        self.stdout.write('seeding data...')

        role_group_nso = models.RoleGroup.objects.create(name='NSO')
        _ = models.Role.objects.create(role_group=role_group_nso, name='HNSO', nonexclusive=True, order_key=1)
        _ = models.Role.objects.create(role_group=role_group_nso, name='JT', order_key=2)
        _ = models.Role.objects.create(role_group=role_group_nso, name='PLT', order_key=3)
        _ = models.Role.objects.create(role_group=role_group_nso, name='PLT', order_key=4)
        _ = models.Role.objects.create(role_group=role_group_nso, name='SBO', order_key=5)
        _ = models.Role.objects.create(role_group=role_group_nso, name='SK', order_key=6)
        _ = models.Role.objects.create(role_group=role_group_nso, name='SK', order_key=7)
        _ = models.Role.objects.create(role_group=role_group_nso, name='PBM', order_key=8)
        _ = models.Role.objects.create(role_group=role_group_nso, name='PBT', order_key=9)
        _ = models.Role.objects.create(role_group=role_group_nso, name='PBT', order_key=10)
        _ = models.Role.objects.create(role_group=role_group_nso, name='ALT', order_key=11)

        role_group_so = models.RoleGroup.objects.create(name='SO')
        _ = models.Role.objects.create(role_group=role_group_so, name='HR', order_key=1)
        _ = models.Role.objects.create(role_group=role_group_so, name='IPR', order_key=2)
        _ = models.Role.objects.create(role_group=role_group_so, name='JR', order_key=3)
        _ = models.Role.objects.create(role_group=role_group_so, name='JR', order_key=4)
        _ = models.Role.objects.create(role_group=role_group_so, name='OPR', order_key=5)
        _ = models.Role.objects.create(role_group=role_group_so, name='OPR', order_key=6)
        _ = models.Role.objects.create(role_group=role_group_so, name='OPR', order_key=7)
        _ = models.Role.objects.create(role_group=role_group_so, name='ALT', order_key=8)

        role_group_tho = models.RoleGroup.objects.create(name='THO')
        _ = models.Role.objects.create(role_group=role_group_tho, name="THR", order_key=1)
        _ = models.Role.objects.create(role_group=role_group_tho, name="THNSO", order_key=2)
        _ = models.Role.objects.create(role_group=role_group_tho, name="GTO", order_key=3)

        league = models.League.objects.create(name='Ceres Roller Derby', slug='ceres')

        # Create a 2-day, 5-game tournament event.
        tournament = models.Event.objects.create(
                name='Belt Bowl',
                league=league,
                slug='belt-bowl',
                start_date=date(2218, 5, 25),
                end_date=date(2218, 5, 26),
                location="Ceres Station Level 6",
        )
        tournament_game_1 = models.Game.objects.create(
                event=tournament,
                name="Game 1",
                start_time=datetime.combine(tournament.start_date, time(10,00)),
                end_time=datetime.combine(tournament.start_date, time(12,00)),
                order_key=1,
        )

        tournament_game_2 = models.Game.objects.create(
                event=tournament,
                name="Game 2",
                start_time=datetime.combine(tournament.start_date, time(12,00)),
                end_time=datetime.combine(tournament.start_date, time(14,00)),
                order_key=2,
        )
        tournament_game_3 = models.Game.objects.create(
                event=tournament,
                name="Game 1",
                start_time=datetime.combine(tournament.start_date, time(16,00)),
                end_time=datetime.combine(tournament.start_date, time(18,00)),
                order_key=3,
        )

        tournament_game_4 = models.Game.objects.create(
                event=tournament,
                name="Game 4",
                start_time=datetime.combine(tournament.end_date, time(12,00)),
                end_time=datetime.combine(tournament.end_date, time(14,00)),
                order_key=4,
        )
        tournament_game_5 = models.Game.objects.create(
                event=tournament,
                name="Game 5",
                start_time=datetime.combine(tournament.end_date, time(14,00)),
                end_time=datetime.combine(tournament.end_date, time(16,00)),
                order_key=5,
        )
        for game in [tournament_game_1,tournament_game_2,tournament_game_3,tournament_game_4,tournament_game_5,]:
            game.role_groups.set([role_group_so, role_group_nso])

        ## Add Role Groups to the tournament
        tournament.role_groups.set([role_group_tho])

        ## Create application forms for the tournament
        app_form = models.ApplicationForm.objects.create(
                event=tournament,
                slug='apply',
                application_kind=models.ApplicationKind.CONFIRM_THEN_ASSIGN,
                application_availability_kind=models.ApplicationAvailabilityKind.BY_DAY,
                hidden=False,
                intro_text="Join the best teams in the Belt! **For beltalowda!**",
                requires_profile_fields=["preferred_name"],
        )
        app_form.role_groups.set([role_group_so, role_group_nso])
        _ = models.Question.objects.create(
                application_form=app_form,
                content="What is your affiliated faction?",
                kind = models.QuestionKind.SELECT_ONE,
                options = ["Loca Griega", "Golden Bough", "OPA", "Free Navy"],
                required=True
        )
        _ = models.Question.objects.create(
                application_form=app_form,
                content="What kinds of kibble do you like?",
                kind = models.QuestionKind.SELECT_MANY,
                options = ["red", "blue", "green"],
                allow_other=True,
                required=True
        )
        _ = models.Question.objects.create(
                application_form=app_form,
                content="What are your special skills?",
                kind=models.QuestionKind.LONG_TEXT,
            )
        _ = models.Question.objects.create(
                application_form=app_form,
                content="What do you think of Marco Inaros?",
                kind=models.QuestionKind.SHORT_TEXT,
            )

        app_form_tho = models.ApplicationForm.objects.create(
                event=tournament,
                slug='apply-tho',
                application_kind=models.ApplicationKind.CONFIRM_ONLY,
                application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT,
                hidden=False,
                intro_text="Join the best teams in the Belt as a tournament leader **For beltalowda!**",
                requires_profile_fields=["preferred_name"],
        )
        app_form_tho.role_groups.set([role_group_tho])
        _ = models.Question.objects.create(
                application_form=app_form_tho,
                content="What do you want to do?",
                kind = models.QuestionKind.LONG_TEXT,
                required=True
        )

        # Create a single-game event.
        singleheader = models.Event.objects.create(
                name='2218-01-19 Game',
                slug='2218-01-19-game',
                league=league,
                start_date=date(2218, 3, 20),
                end_date=date(2218, 3, 20)
        )

        singleheader_game = models.Game.objects.create(
                event=singleheader,
                name="Game",
                start_time=datetime.combine(singleheader.start_date, time(10, 00)),
                end_time=datetime.combine(singleheader.start_date, time(12, 00)),
                order_key=1,
        )
        singleheader_game.role_groups.set([role_group_so, role_group_nso])
        app_form = models.ApplicationForm.objects.create(
                event=singleheader,
                slug='apply',
                application_kind=models.ApplicationKind.CONFIRM_ONLY,
                application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT,
                hidden=False,
                intro_text="Join the best teams in the Belt! **For beltalowda!**",
                requires_profile_fields=["preferred_name"],
        )
        app_form.role_groups.set([role_group_so, role_group_nso])

        self.stdout.write('done.')
