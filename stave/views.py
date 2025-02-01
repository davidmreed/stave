from django.db.models import QuerySet
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseBadRequest,
)
from django.views import generic
from django import views
from django.urls import reverse
from typing import Any, TYPE_CHECKING
from collections.abc import Mapping
import itertools
from uuid import UUID
from . import models
from dataclasses import dataclass, asdict, is_dataclass

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


class MyApplicationsView(generic.ListView):
    template_name = "stave/my_applications.html"
    model = models.Application

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class EventDetailView(generic.DetailView):
    template_name = "stave/event_detail.html"
    model = models.Event

    def get_object(self) -> models.Event:
        return get_object_or_404(
            models.Event,
            league__slug=self.kwargs.get("league"),
            slug=self.kwargs.get("event"),
        )


class LeagueDetailView(generic.DetailView):
    template_name = "stave/league_detail.html"
    model = models.League


class LeagueListView(generic.ListView):
    template_name = "stave/league_list.html"
    model = models.League


class EventListView(generic.ListView):
    template_name = "stave/event_list.html"
    model = models.Event


class ProfileView(generic.TemplateView):
    template_name = "stave/profile.html"


class TypedContextView[T: Mapping[str, Any] | DataclassInstance](generic.DetailView):
    def get_context(self) -> T: ...

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        typed_context = self.get_context()
        if is_dataclass(typed_context):
            context.update(asdict(typed_context))
        else:
            context.update(typed_context)

        return context


@dataclass
class ViewApplicationContext:
    form: models.ApplicationForm
    application: models.Application | None
    user_data: dict[str, str]
    responses_by_id: dict[UUID, models.ApplicationResponse]
    editable: bool


class SingleApplicationView(TypedContextView[ViewApplicationContext]):
    template_name = "stave/view_application.html"
    model = models.Application

    def get_context(self) -> ViewApplicationContext:
        application: models.Application = self.get_object()
        return ViewApplicationContext(
            application=application,
            form=application.form,
            user_data={
                key: str(getattr(application.user, key))
                for key in application.form.requires_profile_fields
            },
            responses_by_id={
                response.question.id: response
                for response in application.responses.all()
            },
            editable=False,
        )


class FormApplicationsView(generic.ListView):
    template_name = "stave/form_applications.html"
    model = models.Application

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        form = get_object_or_404(
            models.ApplicationForm,
            slug=self.kwargs["application_form"],
            event__league__slug=self.kwargs["league"],
        )
        context["form"] = form
        context["applications"] = dict(
            itertools.groupby(
                self.get_queryset().order_by("status"), lambda i: i.status
            )
        )
        return context

    def get_queryset(self) -> QuerySet[models.Application]:
        form = get_object_or_404(
            models.ApplicationForm,
            slug=self.kwargs["application_form"],
            event__league__slug=self.kwargs["league"],
        )
        return super().get_queryset().filter(form=form)


class CrewBuilderView(views.View):
    def get(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
    ) -> HttpResponse:
        print("foo")
        application_form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
        )
        game = application_form.event.games.first()  # TODO
        role_group_crew_assignments = models.RoleGroupCrewAssignment.objects.filter(
            game=game, role_group__in=application_form.role_groups.all()
        )
        effective_assignments_by_role_id = {}
        for rgca in role_group_crew_assignments:
            for crew_assignment in rgca.effective_crew():
                effective_assignments_by_role_id[crew_assignment.role_id] = (
                    crew_assignment
                )

        return render(
            request,
            "stave/crew_builder.html",
            {
                "form": application_form,
                "crew_assignments": effective_assignments_by_role_id,
            },
        )


class CrewBuilderDetailView(views.View):
    """A view rendering the Crew Builder with a list of applications for a given position.
    On GET, renders the view.
    On POST, assigns a role and returns to CrewBuilderView."""

    def get(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
        pk: UUID,
    ) -> HttpResponse:
        application_form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
        )
        role = get_object_or_404(models.Role, pk=pk)
        game = application_form.event.games.first()  # TODO
        applications = application_form.applications.filter(
            roles__name=role.name,
            roles__role_group_id=role.role_group.id,
        )
        # TODO: filter for availability.
        # - Avail for this day or game
        # - Not already assigned.
        # - Accepted, if appropriate.

        return render(
            request,
            "stave/crew_builder.html",
            {"form": application_form, "applications": applications, "role_id": pk},
        )

    def post(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
        pk: UUID,
    ) -> HttpResponse:
        application_id = request.POST.get("application_id")
        if not application_id:
            return HttpResponseBadRequest("invalid application id")

        application_form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
        )
        game = application_form.event.games.first()  # TODO
        applications = application_form.applications.filter(
            id=application_id,
            roles__id=pk,
        )
        if len(applications) != 1:
            return HttpResponseBadRequest("multiple matching applications")

        role_assignment, _ = models.CrewAssignment.objects.get_or_create(
            role_id=pk,
            crew=game.role_group_crew_assignments.filter(role_group__roles__id=pk)[
                0
            ].crew_overrides,
        )

        role_assignment.user = applications[0].user
        role_assignment.save()

        # Redirect the user to the base Crew Builder for this crew
        return HttpResponseRedirect(
            reverse("crew-builder", args=[league, event_slug, application_form_slug])
        )


class ApplicationFormView(views.View):
    def get(
        self, request: HttpRequest, application_form: str, event: str, league: str
    ) -> HttpResponse:
        form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form,
            event__slug=event,
            event__league__slug=league,
        )

        context = ViewApplicationContext(
            application=None,
            form=form,
            user_data={
                models.User._meta.get_field(key).verbose_name.title(): str(
                    getattr(request.user, key)
                )
                for key in form.requires_profile_fields
            }
            if request.user.is_authenticated
            else {},
            responses_by_id={},
            editable=request.user.is_authenticated,
        )

        return render(request, "stave/view_application.html", asdict(context))

    def post(
        self, request: HttpRequest, application_form: str, event: str, league: str
    ) -> HttpResponse:
        # TODO: if this is an edit to an existing application, replace data.
        app = None

        with transaction.atomic():
            form = get_object_or_404(
                models.ApplicationForm,
                slug=application_form,
                event__slug=event,
                event__league__slug=league,
            )

            # Construct and persist an Application, ApplicationResponse, and RoleAssignments

            app = models.Application(
                form=form, user=request.user, status=models.ApplicationStatus.APPLIED
            )

            # Pull out Availability information
            if (
                form.application_availability_kind
                == models.ApplicationAvailabilityKind.BY_DAY
            ):
                app.availability_by_day = [
                    day for day in form.event.days() if f"day-{day}" in request.POST
                ]
            elif (
                form.application_availability_kind
                == models.ApplicationAvailabilityKind.BY_GAME
            ):
                app.availability_by_game = [  # TODO
                    game
                    for game in form.event.games.all()
                    if f"game-{game.id}" in request.POST
                ]
            app.roles.set(
                [
                    role
                    for role in models.Role.objects.filter(
                        role_group__in=form.role_groups.all()
                    )
                    if f"role-{role.id}" in request.POST
                ]
            )
            app.save()

            # Question answers
            for question in form.form_questions.all():
                if str(question.id) in request.POST:
                    values = request.POST.getlist(str(question.id))
                    if not values or (
                        len(values) != 1
                        and question.kind != question.QuestionKind.SELECT_MANY
                    ):
                        return HttpResponse(400)
                    if question.kind in (
                        models.QuestionKind.SHORT_TEXT,
                        models.QuestionKind.LONG_TEXT,
                    ):
                        content = values[0]
                    else:
                        # The content of `values` should be indices into the `options` array
                        # for this question
                        try:
                            answers = [question.options[int(v)] for v in values]
                        except (ValueError, IndexError):
                            return HttpResponse(400)

                        if f"{question.id}-other" in request.POST:
                            if not question.allow_other or not request.POST.get(
                                f"{question.id}-other-value"
                            ):
                                return HttpResponse("bad other")
                            else:
                                answers.append(
                                    request.POST[f"{question.id}-other-value"]
                                )

                        content = answers if len(answers) > 1 else answers[0]

                    if question.required and not content:
                        return HttpResponse("Missing content")

                    response = models.ApplicationResponse(
                        application=app, question=question, content=content
                    )
                    response.save()
                else:
                    return HttpResponse(f"missing question {question.content}")

            return HttpResponseRedirect(reverse("view-application", args=[app.id]))
