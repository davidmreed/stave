from django.core.management.base import BaseCommand
from stave import models
from datetime import datetime, date, time

class Command(BaseCommand):
    help = "seed database for testing and development."

    def handle(self, *_args, **_kwargs): # type: ignore
        self.stdout.write('seeding data...')

        role_group_nso = models.RoleGroup.objects.create(name='NSO')
        role_hnso = models.Role.objects.create(role_group=role_group_nso, name='HNSO', nonexclusive=True, order_key=1)
        role_jt = models.Role.objects.create(role_group=role_group_nso, name='JT', order_key=2)
        role_plt = models.Role.objects.create(role_group=role_group_nso, name='PLT', order_key=3)
        role_plt2 = models.Role.objects.create(role_group=role_group_nso, name='PLT', order_key=4)
        role_sbo = models.Role.objects.create(role_group=role_group_nso, name='SBO', order_key=5)
        role_sk = models.Role.objects.create(role_group=role_group_nso, name='SK', order_key=6)
        role_sk2 = models.Role.objects.create(role_group=role_group_nso, name='SK', order_key=7)
        role_pbm = models.Role.objects.create(role_group=role_group_nso, name='PBM', order_key=8)
        role_pbt = models.Role.objects.create(role_group=role_group_nso, name='PBT', order_key=9)
        role_pbt2 = models.Role.objects.create(role_group=role_group_nso, name='PBT', order_key=10)
        role_alt = models.Role.objects.create(role_group=role_group_nso, name='ALT', order_key=11)

        role_group_so = models.RoleGroup.objects.create(name='SO')
        role_hr = models.Role.objects.create(role_group=role_group_so, name='HR', order_key=1)
        role_ipr = models.Role.objects.create(role_group=role_group_so, name='IPR', order_key=2)
        role_jr = models.Role.objects.create(role_group=role_group_so, name='JR', order_key=3)
        role_jr2 = models.Role.objects.create(role_group=role_group_so, name='JR', order_key=4)
        role_opr = models.Role.objects.create(role_group=role_group_so, name='OPR', order_key=5)
        role_opr2 = models.Role.objects.create(role_group=role_group_so, name='OPR', order_key=6)
        role_opr3 = models.Role.objects.create(role_group=role_group_so, name='OPR', order_key=7)
        role_altref = models.Role.objects.create(role_group=role_group_so, name='ALT', order_key=8)

        role_group_tho = models.RoleGroup.objects.create(name='THO')
        role_thr = models.Role.objects.create(role_group=role_group_tho, name="THR", order_key=1)
        role_thnso = models.Role.objects.create(role_group=role_group_tho, name="THNSO", order_key=2)
        role_gto = models.Role.objects.create(role_group=role_group_tho, name="GTO", order_key=3)

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
        app_form_question_faction = models.Question.objects.create(
                application_form=app_form,
                content="What is your affiliated faction?",
                kind = models.QuestionKind.SELECT_ONE,
                options = ["Loca Griega", "Golden Bough", "OPA", "Free Navy"],
                required=True
        )
        app_form_question_kibble = models.Question.objects.create(
                application_form=app_form,
                content="What kinds of kibble do you like?",
                kind = models.QuestionKind.SELECT_MANY,
                options = ["red", "blue", "green"],
                allow_other=True,
                required=True
        )
        app_form_question_skills = models.Question.objects.create(
                application_form=app_form,
                content="What are your special skills?",
                kind=models.QuestionKind.LONG_TEXT,
            )
        app_form_question_marco = models.Question.objects.create(
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
                intro_text="Join the best teams in the Belt as a tournament leader. **For beltalowda!**",
                requires_profile_fields=["preferred_name"],
        )
        app_form_tho.role_groups.set([role_group_tho])
        app_form_tho_question = models.Question.objects.create(
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
        singleheader_app_form = models.ApplicationForm.objects.create(
                event=singleheader,
                slug='apply',
                application_kind=models.ApplicationKind.CONFIRM_ONLY,
                application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT,
                hidden=False,
                intro_text="Join the best teams in the Belt! **For beltalowda!**",
                requires_profile_fields=["preferred_name"],
        )
        singleheader_app_form.role_groups.set([role_group_so, role_group_nso])

        # Create some users
        admin = models.User.objects.create(
                username="admin",
                preferred_name="admin",
                is_staff=True,
                is_superuser=True
        )
        admin.set_password("root")
        admin.save()
        drummer = models.User.objects.create(
            username="drummer",
            preferred_name="bossmang",
            pronouns="she/they",
        )
        josep = models.User.objects.create(
                username="josep",
                preferred_name="sasaje",
                pronouns="he/him"
        )
        michio = models.User.objects.create(
                username="michio",
                preferred_name="Michmuch",
                pronouns="she/her"
        )
        rosenfeld = models.User.objects.create(
                username="rosenfeld",
                preferred_name="Go-long",
                pronouns = "they/them",
            )

        # And applications
        drummer_app = models.Application.objects.create(
                form=app_form_tho,
                user=drummer,
                status=models.ApplicationStatus.APPLIED
        )
        drummer_app.roles.set([role_thnso])
        _ = models.ApplicationResponse(
            application=drummer_app,
            question=app_form_tho_question,
            content="Live shamed and die empty"
        )

        josep_app = models.Application.objects.create(
                form=app_form,
                user=josep,
                status=models.ApplicationStatus.APPLIED,
            )
        josep_app.roles.set([role_hnso, role_jt, role_plt, role_sbo, role_pbm, role_sk, role_pbt])
        _ = models.ApplicationResponse(
                application=josep_app,
                question=app_form_question_faction,
                content="OPA",
        )

        _ = models.ApplicationResponse(
                application=josep_app,
                question=app_form_question_kibble,
                content=["red", "blue"],
        )
        _ = models.ApplicationResponse(
                application=josep_app,
                question=app_form_question_skills,
                content="Piloting",
                )
        _ = models.ApplicationResponse(
                application=josep_app,
                question=app_form_question_marco,
                content="I hate that guy",
        )
        self.stdout.write('done.')
