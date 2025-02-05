from django.db.models import QuerySet, Q
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
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from typing import Any, TYPE_CHECKING
from collections.abc import Mapping
import itertools
from uuid import UUID
from . import models, settings, forms
from dataclasses import dataclass, asdict, is_dataclass
from django.contrib.auth.mixins import LoginRequiredMixin

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


class MyApplicationsView(LoginRequiredMixin, generic.ListView):
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


class EventUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = "stave/league_edit.html"
    form_class = forms.EventForm

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["request"] = self.request
        return kwargs

    def get_queryset(self) -> QuerySet[models.Event]:
        return models.Event.objects.filter(
            league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
            league__user_permissions__user=self.request.user,
        ).distinct()

    def get_object(self) -> models.Event:
        return (
            self.get_queryset()
            .filter(league__slug=self.kwargs["league"], slug=self.kwargs["event"])
            .get()
        )


class EventCreateView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = "stave/league_edit.html"
    form_class = forms.EventForm

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form: forms.EventForm) -> HttpResponse:
        ret = super().form_valid(form)

        # Make the current user a league manager
        _ = models.LeagueUserPermission.objects.create(
            league=self.object.league,
            user=self.request.user,
            permission=models.UserPermission.EVENT_MANAGER,
        )

        return ret


class LeagueUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = "stave/league_edit.html"
    form_class = forms.LeagueForm

    def get_queryset(self) -> QuerySet[models.League]:
        return models.League.objects.filter(
            user_permissions__permission=models.UserPermission.LEAGUE_MANAGER,
            user_permissions__user=self.request.user,
        ).distinct()


class LeagueCreateView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = "stave/league_edit.html"
    form_class = forms.LeagueForm

    def form_valid(self, form: forms.LeagueForm) -> HttpResponse:
        ret = super().form_valid(form)

        # Make the current user a league manager
        _ = models.LeagueUserPermission.objects.create(
            league=self.object,
            user=self.request.user,
            permission=models.UserPermission.LEAGUE_MANAGER,
        )

        return ret


class LeagueDetailView(generic.DetailView):
    template_name = "stave/league_detail.html"
    model = models.League


class LeagueListView(generic.ListView):
    template_name = "stave/league_list.html"
    model = models.League


class EventListView(generic.ListView):
    template_name = "stave/event_list.html"
    model = models.Event


class FormCreateView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = "stave/league_edit.html"
    form_class = forms.ApplicationFormForm


class ProfileView(LoginRequiredMixin, generic.TemplateView):
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


class SingleApplicationView(
    LoginRequiredMixin, TypedContextView[ViewApplicationContext]
):
    template_name = "stave/view_application.html"
    model = models.Application

    def get_queryset(self) -> QuerySet[models.Application]:
        return models.Application.objects.filter(
            Q(user=self.request.user)
            | Q(
                form__event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
                form__event__league__user_permissions__user=self.request.user,
            )
        )

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


class FormApplicationsView(LoginRequiredMixin, generic.ListView):
    template_name = "stave/form_applications.html"
    model = models.Application

    def get_context_data(self, **kwargs: dict[str, Any]):
        context = super().get_context_data(**kwargs)
        form = get_object_or_404(
            models.ApplicationForm,
            slug=self.kwargs["application_form_slug"],
            event__slug=self.kwargs["event_slug"],
            event__league__slug=self.kwargs["league_slug"],
        )
        context["form"] = form
        context["applications"] = {
            key: list(group)
            for key, group in itertools.groupby(
                self.get_queryset().order_by("status"), lambda i: i.status
            )
        }
        context["ApplicationStatus"] = models.ApplicationStatus
        return context

    def get_queryset(self) -> QuerySet[models.Application]:
        form = get_object_or_404(
            models.ApplicationForm,
            slug=self.kwargs["application_form_slug"],
            event__slug=self.kwargs["event_slug"],
            event__league__slug=self.kwargs["league_slug"],
        )
        return (
            super()
            .get_queryset()
            .filter(
                Q(user=self.request.user)
                | Q(
                    form__event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
                    form__event__league__user_permissions__user=self.request.user,
                ),
                form=form,
            )
        )


class ApplicationStatusView(LoginRequiredMixin, views.View):
    def post(
        self, request: HttpRequest, pk: UUID, status: models.ApplicationStatus
    ) -> HttpResponse:
        application = get_object_or_404(
            models.Application,
            pk=pk,
            form__event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
            form__event__league__user_permissions__user=self.request.user,
        )
        application.status = status  # TODO: verify
        application.save()

        redirect_url = request.POST.get("redirect_url")
        if redirect_url and url_has_allowed_host_and_scheme(
            redirect_url, settings.ALLOWED_HOSTS
        ):
            return HttpResponseRedirect(redirect_url)

        return HttpResponseRedirect("/")


class CrewBuilderView(LoginRequiredMixin, views.View):
    def get(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
    ) -> HttpResponse:
        application_form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
            event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
            event__league__user_permissions__user=self.request.user,
        )
        effective_assignments_by_game_by_role_id = {}
        for game in application_form.event.games.all():
            effective_assignments_by_game_by_role_id[game.id] = {}
            for rgca in game.role_group_crew_assignments.filter(
                role_group__in=application_form.role_groups.all()
            ):
                for crew_assignment in rgca.effective_crew():
                    effective_assignments_by_game_by_role_id[game.id][
                        crew_assignment.role_id
                    ] = crew_assignment

        return render(
            request,
            "stave/crew_builder.html",
            {
                "form": application_form,
                "crew_assignments": effective_assignments_by_game_by_role_id,
            },
        )


class CrewBuilderDetailView(LoginRequiredMixin, views.View):
    """A view rendering the Crew Builder with a list of applications for a given position.
    On GET, renders the view.
    On POST, assigns a role and returns to CrewBuilderView."""

    def get(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
        game_id: UUID,
        role_id: UUID,
    ) -> HttpResponse:
        application_form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
            event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
            event__league__user_permissions__user=self.request.user,
        )
        role = get_object_or_404(models.Role, pk=role_id)
        game = get_object_or_404(models.Game, pk=game_id)
        # TODO: verification
        applications = list(application_form.get_applications_for_role(role, game))
        return render(
            request,
            "stave/crew_builder_detail.html",
            {
                "form": application_form,
                "applications": applications,
                "game": game,
                "role": role,
            },
        )

    def post(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
        game_id: UUID,
        role_id: UUID,
    ) -> HttpResponse:
        application_id = request.POST.get("application_id")
        if not application_id:
            return HttpResponseBadRequest("invalid application id")

        application_form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
            event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
            event__league__user_permissions__user=self.request.user,
        )
        role = get_object_or_404(models.Role, pk=role_id)
        game = get_object_or_404(models.Game, pk=game_id)
        # TODO: verification
        applications = application_form.applications.filter(
            id=application_id,
            roles__name=role.name,
        )
        if len(applications) != 1:
            return HttpResponseBadRequest("multiple matching applications")

        role_group_crew_assignment = game.role_group_crew_assignments.filter(
            role_group__roles__id=role_id
        ).first()
        if not role_group_crew_assignment.crew_overrides:
            role_group_crew_assignment.crew_overrides = models.Crew.objects.create(
                is_override=True,
                role_group=role_group_crew_assignment.role_group,
                event=game.event,
            )
            role_group_crew_assignment.save()

        _ = models.CrewAssignment.objects.get_or_create(
            role_id=role_id,
            crew=role_group_crew_assignment.crew_overrides,
            user=applications[0].user,
        )

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

    @login_required
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
                        return HttpResponseBadRequest()
                    if question.kind in (
                        models.QuestionKind.SHORT_TEXT,
                        models.QuestionKind.LONG_TEXT,
                    ):
                        content = values
                    else:
                        # The content of `values` should be indices into the `options` array
                        # for this question
                        try:
                            answers = [question.options[int(v)] for v in values]
                        except (ValueError, IndexError):
                            return HttpResponseBadRequest()

                        if f"{question.id}-other" in request.POST:
                            if not question.allow_other or not request.POST.get(
                                f"{question.id}-other-value"
                            ):
                                return HttpResponse("bad other")
                            else:
                                answers.append(
                                    request.POST[f"{question.id}-other-value"]
                                )

                        content = answers

                    if question.required and not content:
                        return HttpResponseBadRequest("Missing content")

                    response = models.ApplicationResponse(
                        application=app, question=question, content=content
                    )
                    response.save()
                else:
                    return HttpResponseBadRequest(
                        f"missing question {question.content}"
                    )

            return HttpResponseRedirect(reverse("view-application", args=[app.id]))
