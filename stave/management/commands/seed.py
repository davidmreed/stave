from django.core.management.base import BaseCommand
from stave import models
from datetime import datetime, date, time, timezone
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = "seed database for testing and development."

    def handle(self, *_args, **_kwargs):  # type: ignore
        self.stdout.write("seeding data...")

        league = models.League.objects.create(
            name="Ceres Roller Derby",
            slug="ceres",
            location="Ceres Station, The Belt",
            description="The **best** roller derby in the Belt and Outer Planets",
            website="https://derby.ceres.belt",
            enabled=True,
        )
        role_group_nso = models.RoleGroup.objects.create(name="NSO", league=league)
        role_hnso = models.Role.objects.create(
            role_group=role_group_nso, name="HNSO", nonexclusive=True, order_key=1
        )
        role_jt = models.Role.objects.create(
            role_group=role_group_nso, name="JT", order_key=2
        )
        role_plt = models.Role.objects.create(
            role_group=role_group_nso, name="PLT", order_key=3
        )
        role_plt2 = models.Role.objects.create(
            role_group=role_group_nso, name="PLT", order_key=4
        )
        role_sbo = models.Role.objects.create(
            role_group=role_group_nso, name="SBO", order_key=5
        )
        role_sk = models.Role.objects.create(
            role_group=role_group_nso, name="SK", order_key=6
        )
        role_sk2 = models.Role.objects.create(
            role_group=role_group_nso, name="SK", order_key=7
        )
        role_pbm = models.Role.objects.create(
            role_group=role_group_nso, name="PBM", order_key=8
        )
        role_pbt = models.Role.objects.create(
            role_group=role_group_nso, name="PBT", order_key=9
        )
        role_pbt2 = models.Role.objects.create(
            role_group=role_group_nso, name="PBT", order_key=10
        )
        role_alt = models.Role.objects.create(
            role_group=role_group_nso, name="ALT", order_key=11
        )

        role_group_so = models.RoleGroup.objects.create(name="SO", league=league)
        role_hr = models.Role.objects.create(
            role_group=role_group_so, name="HR", order_key=1
        )
        role_ipr = models.Role.objects.create(
            role_group=role_group_so, name="IPR", order_key=2
        )
        role_jr = models.Role.objects.create(
            role_group=role_group_so, name="JR", order_key=3
        )
        role_jr2 = models.Role.objects.create(
            role_group=role_group_so, name="JR", order_key=4
        )
        role_opr = models.Role.objects.create(
            role_group=role_group_so, name="OPR", order_key=5
        )
        role_opr2 = models.Role.objects.create(
            role_group=role_group_so, name="OPR", order_key=6
        )
        role_opr3 = models.Role.objects.create(
            role_group=role_group_so, name="OPR", order_key=7
        )
        role_altref = models.Role.objects.create(
            role_group=role_group_so, name="ALT", order_key=8
        )

        role_group_tho = models.RoleGroup.objects.create(name="THO", league=league)
        role_thr = models.Role.objects.create(
            role_group=role_group_tho, name="THR", order_key=1
        )
        role_thnso = models.Role.objects.create(
            role_group=role_group_tho, name="THNSO", order_key=2
        )
        role_gto = models.Role.objects.create(
            role_group=role_group_tho, name="GTO", order_key=3
        )

        # Create a 2-day, 5-game tournament event.
        tournament = models.Event.objects.create(
            name="Outer Planets Throwdown",
            league=league,
            status=models.EventStatus.OPEN,
            slug="outer-planets-throwdown",
            start_date=date(2218, 5, 25),
            end_date=date(2218, 5, 26),
            location="Ceres Station Level 6",
        )
        tournament_game_1 = models.Game.objects.create(
            event=tournament,
            name="Game 1",
            start_time=datetime.combine(
                tournament.start_date, time(10, 00), timezone.utc
            ),
            end_time=datetime.combine(
                tournament.start_date, time(12, 00), timezone.utc
            ),
            order_key=1,
        )

        tournament_game_2 = models.Game.objects.create(
            event=tournament,
            name="Game 2",
            start_time=datetime.combine(
                tournament.start_date, time(12, 00), timezone.utc
            ),
            end_time=datetime.combine(
                tournament.start_date, time(14, 00), timezone.utc
            ),
            order_key=2,
        )
        tournament_game_3 = models.Game.objects.create(
            event=tournament,
            name="Game 1",
            start_time=datetime.combine(
                tournament.start_date, time(16, 00), timezone.utc
            ),
            end_time=datetime.combine(
                tournament.start_date, time(18, 00), timezone.utc
            ),
            order_key=3,
        )

        tournament_game_4 = models.Game.objects.create(
            event=tournament,
            name="Game 4",
            start_time=datetime.combine(
                tournament.end_date, time(12, 00), timezone.utc
            ),
            end_time=datetime.combine(tournament.end_date, time(14, 00), timezone.utc),
            order_key=4,
        )
        tournament_game_5 = models.Game.objects.create(
            event=tournament,
            name="Game 5",
            start_time=datetime.combine(
                tournament.end_date, time(14, 00), timezone.utc
            ),
            end_time=datetime.combine(tournament.end_date, time(16, 00), timezone.utc),
            order_key=5,
        )

        ## Add Role Groups to the tournament
        tournament.role_groups.set([role_group_tho, role_group_so, role_group_nso])

        for game in [
            tournament_game_1,
            tournament_game_2,
            tournament_game_3,
            tournament_game_4,
            tournament_game_5,
        ]:
            for role_group in [role_group_so, role_group_nso]:
                _ = models.RoleGroupCrewAssignment.objects.create(
                    game=game, role_group=role_group
                )

        _ = models.EventRoleGroupCrewAssignment.objects.create(
            event=tournament,
            role_group=role_group_tho,
        )

        ## Create application forms for the tournament
        app_form = models.ApplicationForm.objects.create(
            event=tournament,
            slug="apply",
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
            kind=models.QuestionKind.SELECT_ONE,
            options=["Loca Griega", "Golden Bough", "OPA", "Free Navy"],
            required=True,
            order_key=1,
        )
        app_form_question_kibble = models.Question.objects.create(
            application_form=app_form,
            content="What kinds of kibble do you like?",
            kind=models.QuestionKind.SELECT_MANY,
            options=["red", "blue", "green"],
            allow_other=True,
            required=True,
            order_key=2,
        )
        app_form_question_skills = models.Question.objects.create(
            application_form=app_form,
            content="What are your special skills?",
            kind=models.QuestionKind.LONG_TEXT,
            order_key=3,
        )
        app_form_question_marco = models.Question.objects.create(
            application_form=app_form,
            content="What do you think of Marco Inaros?",
            kind=models.QuestionKind.SHORT_TEXT,
            order_key=4,
        )

        app_form_tho = models.ApplicationForm.objects.create(
            event=tournament,
            slug="apply-tho",
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
            kind=models.QuestionKind.LONG_TEXT,
            required=True,
            order_key=1,
        )

        # Create a single-game event.
        singleheader = models.Event.objects.create(
            name="2218-01-19 Game",
            slug="2218-01-19-game",
            status=models.EventStatus.OPEN,
            league=league,
            start_date=date(2218, 3, 20),
            end_date=date(2218, 3, 20),
        )

        singleheader_game = models.Game.objects.create(
            event=singleheader,
            name="Game",
            start_time=datetime.combine(
                singleheader.start_date, time(10, 00), timezone.utc
            ),
            end_time=datetime.combine(
                singleheader.start_date, time(12, 00), timezone.utc
            ),
            order_key=1,
        )
        for role_group in [role_group_so, role_group_nso]:
            _ = models.RoleGroupCrewAssignment.objects.create(
                game=singleheader_game, role_group=role_group
            )
        singleheader_app_form = models.ApplicationForm.objects.create(
            event=singleheader,
            slug="apply",
            application_kind=models.ApplicationKind.CONFIRM_ONLY,
            application_availability_kind=models.ApplicationAvailabilityKind.WHOLE_EVENT,
            hidden=False,
            intro_text="Join the best teams in the Belt! **For beltalowda!**",
            requires_profile_fields=["preferred_name"],
        )
        singleheader_app_form.role_groups.set([role_group_so, role_group_nso])

        # Create some users
        def create_user(
            username: str, preferred_name: str, admin: bool, pronouns: str
        ) -> models.User:
            user = models.User.objects.create(
                username=username,
                preferred_name=preferred_name,
                pronouns=pronouns,
                is_staff=admin,
                is_superuser=admin,
            )
            user.set_password(username)
            user.save()
            _ = EmailAddress.objects.create(
                user=user, email=f"{username}@example.com", verified=True, primary=True
            )
            return user

        admin = create_user("admin", "admin", True, "he/him")
        _ = models.LeagueUserPermission.objects.create(
            user=admin, league=league, permission=models.UserPermission.EVENT_MANAGER
        )
        _ = models.LeagueUserPermission.objects.create(
            user=admin, league=league, permission=models.UserPermission.LEAGUE_MANAGER
        )
        drummer = create_user("drummer", "bossmang", False, "she/they")
        josep = create_user("josep", "sasaje", False, "he/him")
        michio = create_user("michio", "Michmuch", False, "she/her")
        rosenfeld = create_user(
            username="rosenfeld",
            preferred_name="Go-long",
            admin=False,
            pronouns="they/them",
        )
        dawes = create_user(
            username="dawes", preferred_name="anderson", admin=False, pronouns="he/him"
        )
        johnson = create_user(
            username="johnson",
            preferred_name="tychoman",
            admin=False,
            pronouns="he/him",
        )
        miller = create_user(
            username="miller", preferred_name="joe", admin=False, pronouns="he/him"
        )
        bull = create_user(
            username="cdebaca", preferred_name="Bull", admin=False, pronouns="he/him"
        )
        liang = create_user(
            username="liang", preferred_name="walker", admin=False, pronouns="he/him"
        )
        oksana = create_user(
            username="oksana", preferred_name="oksana", admin=False, pronouns="she/her"
        )

        # And applications
        drummer_app_tho = models.Application.objects.create(
            form=app_form_tho, user=drummer, status=models.ApplicationStatus.APPLIED
        )
        drummer_app_tho.roles.set([role_thnso])

        _ = models.ApplicationResponse.objects.create(
            application=drummer_app_tho,
            question=app_form_tho_question,
            content=["Live shamed and die empty"],
        )

        def create_tournament_app(
            user: models.User,
            roles: list[models.Role],
            avail: list[str],
            faction: str,
            kibble: list[str],
            skills: str,
            marco: str,
        ):
            app = models.Application.objects.create(
                form=app_form,
                user=user,
                status=models.ApplicationStatus.INVITED,
                availability_by_day=avail,
            )
            app.roles.set(roles)
            _ = models.ApplicationResponse.objects.create(
                application=app,
                question=app_form_question_faction,
                content=[faction],
            )

            _ = models.ApplicationResponse.objects.create(
                application=app,
                question=app_form_question_kibble,
                content=kibble,
            )
            _ = models.ApplicationResponse.objects.create(
                application=app,
                question=app_form_question_skills,
                content=[skills],
            )
            _ = models.ApplicationResponse.objects.create(
                application=app,
                question=app_form_question_marco,
                content=[marco],
            )

        create_tournament_app(
            josep,
            [role_hnso, role_jt, role_plt, role_sbo, role_pbm, role_sk, role_pbt],
            [d for d in app_form.event.days()],
            "OPA",
            ["red", "blue"],
            "Piloting",
            "Hate that guy",
        )

        create_tournament_app(
            drummer,
            [role_hnso, role_jt, role_plt, role_sbo, role_pbm, role_sk, role_pbt],
            [d for d in app_form.event.days()],
            "OPA",
            ["red", "blue"],
            "Piloting",
            "The worst",
        )
        create_tournament_app(
            michio,
            [role_jt, role_plt, role_sk, role_pbt],
            [d for d in app_form.event.days()],
            "OPA",
            ["red", "green"],
            "Piloting",
            "Scary",
        )
        create_tournament_app(
            rosenfeld,
            [role_jt, role_plt, role_pbm, role_sbo, role_sk, role_pbt],
            [d for d in app_form.event.days()],
            "Free Navy",
            ["red", "green"],
            "Administration",
            "Well-intentioned",
        )
        create_tournament_app(
            miller,
            [role_pbm, role_pbt],
            [d for d in app_form.event.days()],
            "OPA",
            ["red"],
            "detecting",
            "evil SOB",
        )
        create_tournament_app(
            dawes,
            [role_hnso, role_plt, role_jt],
            [d for d in app_form.event.days()],
            "OPA",
            ["red"],
            "leadership",
            "useful",
        )
        create_tournament_app(
            johnson,
            [role_hnso, role_jt, role_plt, role_sbo, role_pbm, role_sk, role_pbt],
            [d for d in app_form.event.days()],
            "OPA",
            ["red"],
            "starship construction",
            "useful",
        )
        create_tournament_app(
            bull,
            [role_sbo, role_sk],
            [d for d in app_form.event.days()],
            "OPA",
            ["red", "blue"],
            "security",
            "evil",
        )
        create_tournament_app(
            liang,
            [role_sk, role_pbt],
            [d for d in app_form.event.days()],
            "OPA",
            ["red", "blue"],
            "piracy",
            "evil",
        )
        create_tournament_app(
            oksana,
            [role_jt, role_sk, role_pbt],
            [d for d in app_form.event.days()],
            "OPA",
            ["red", "blue"],
            "navigation",
            "evil",
        )

        self.stdout.write("done.")
