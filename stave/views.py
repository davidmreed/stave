import dataclasses
import itertools
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django import views
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.forms import modelform_factory
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy
from django.views import generic

from stave.templates.stave import contexts

from . import forms, models, settings

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


class TypedContextMixin[T: dict[str, Any] | DataclassInstance]:
    def get_context(self) -> T: ...

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)

        typed_context = self.get_context()
        if is_dataclass(typed_context):
            _ = context.update(asdict(typed_context))
        else:
            _ = context.update(typed_context)

        return context


class MyApplicationsView(LoginRequiredMixin, generic.ListView):
    template_name = "stave/my_applications.html"
    model = models.Application

    def get_queryset(self) -> QuerySet[models.Application]:
        return super().get_queryset().filter(user=self.request.user)


class HomeView(generic.TemplateView):
    template_name = "stave/home.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        application_forms = models.ApplicationForm.objects.listed(self.request.user)
        if self.request.user.is_authenticated:
            application_forms = application_forms.exclude(
                applications__user=self.request.user
            )

            applications = models.Application.objects.filter(
                user=self.request.user, form__event__start_date__gt=datetime.now()
            )
            events = models.Event.objects.filter(
                league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
                league__user_permissions__user=self.request.user,
            ).distinct()
        else:
            applications = []
            events = []

        context["application_forms"] = application_forms
        context["events"] = events
        context["applications"] = applications

        return context


class EventDetailView(
    TypedContextMixin[contexts.EventDetailInputs], generic.DetailView
):
    template_name = "stave/event_detail.html"
    model = models.Event
    slug_url_kwarg = "event"

    def get_context(self) -> contexts.EventDetailInputs:
        return contexts.EventDetailInputs(
            event=self.get_object(),
            application_forms=models.ApplicationForm.objects.listed(
                self.request.user
            ).filter(event=self.get_object()),
        )

    def get_queryset(self) -> QuerySet[models.Event]:
        return models.Event.objects.visible(user=self.request.user).filter(
            league__slug=self.kwargs["league"]
        )


class EventUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = "stave/league_edit.html"
    form_class = forms.EventForm
    slug_url_kwarg = "event"

    def get_queryset(self) -> QuerySet[models.Event]:
        return models.Event.objects.manageable(self.request.user).filter(
            league__slug=self.kwargs["league"],
        )


class EventCreateView(
    LoginRequiredMixin,
    TypedContextMixin[contexts.TemplateSelectorInputs],
    generic.edit.CreateView,
):
    template_name = "stave/template_selector.html"
    league: models.League
    selected_template: models.EventTemplate | None

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)

        self.league = get_object_or_404(
            models.League.objects.event_manageable(self.request.user),
            slug=self.kwargs.get("league"),
        )
        self.selected_template = None
        if template_id := request.POST.get("template_id"):
            self.selected_template = get_object_or_404(
                self.league.event_templates.all(), pk=template_id
            )

    def get_form_class(self) -> type:
        if self.selected_template:
            return forms.EventFromTemplateForm

        return forms.EventForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["league"] = self.league

        # If we're just moving to the second screen, we don't want
        # to validate the form yet (since the user hasn't had a chance
        # to do any entry).

        if "slug" not in self.request.POST and "data" in kwargs:
            # This form submission wasn't from a page that had the form rendered.
            del kwargs["data"]
            del kwargs["files"]

        return kwargs

    def get_context(self) -> contexts.TemplateSelectorInputs:
        return contexts.TemplateSelectorInputs(
            templates=self.league.event_templates.all(),
            object_type="Event",
            selected_template=self.selected_template,
            require_template_selection_first=True,
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not self.selected_template:
            # This is the first stage of the form, where the user has to select a template.
            # We don't want to call form_valid() because the user hasn't
            # actually filled out the model form yet.
            self.object = None
            return self.render_to_response(self.get_context_data())

        return super().post(request, *args, **kwargs)

    def form_valid(
        self, form: forms.EventForm | forms.EventFromTemplateForm
    ) -> HttpResponse:
        with transaction.atomic():
            if self.selected_template:
                # We're cloning an event template.
                event = self.selected_template.clone(**form.cleaned_data)
            else:
                event = form.save(commit=False)
                event.league = self.league
                event.save()

            self.object = event

            return HttpResponseRedirect(self.get_success_url())


class CrewCreateView(LoginRequiredMixin, views.View):
    def post(
        self, request: HttpRequest, league_slug: str, event_slug: str, form_slug: str
    ) -> HttpResponse:
        form = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            event__league__slug=league_slug,
            event__slug=event_slug,
            slug=form_slug,
        )
        role_group = get_object_or_404(
            form.role_groups.all(), pk=request.POST.get("role_group_id")
        )

        name = gettext_lazy("{} Crew {}").format(
            role_group,
            models.Crew.objects.filter(
                event=form.event, kind=models.CrewKind.GAME_CREW, role_group=role_group
            ).count()
            + 1,
        )

        _ = models.Crew.objects.create(
            kind=models.CrewKind.GAME_CREW,
            event=form.event,
            role_group=role_group,
            name=name,
        )
        redirect_url = request.POST.get("redirect_url")
        if redirect_url and url_has_allowed_host_and_scheme(
            redirect_url, settings.ALLOWED_HOSTS
        ):
            return HttpResponseRedirect(redirect_url)

        return HttpResponseRedirect(form.get_absolute_url())


class GameUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = "stave/league_edit.html"
    form_class = forms.GameForm

    def get_queryset(self) -> QuerySet[models.Game]:
        return models.Game.objects.manageable(self.request.user)


class GameCreateView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = "stave/league_edit.html"
    form_class = forms.GameForm

    def get(
        self, request: HttpRequest, league_slug: str, event_slug: str, *args, **kwargs
    ) -> HttpResponse:
        _ = get_object_or_404(
            models.League.objects.event_manageable(request.user),
            slug=league_slug,
        )

        return super().get(request, *args, **kwargs)

    def form_valid(self, form: forms.GameForm) -> HttpResponse:
        event = get_object_or_404(
            models.Event.objects.manageable(self.request.user),
            league__slug=self.kwargs["league_slug"],
            slug=self.kwargs["event_slug"],
        )

        form.instance.event_id = event.id
        return super().form_valid(form)


class LeagueUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = "stave/league_edit.html"
    form_class = forms.LeagueForm

    def get_queryset(self) -> QuerySet[models.League]:
        return models.League.objects.manageable(self.request.user)


class LeagueCreateView(
    LoginRequiredMixin,
    TypedContextMixin[contexts.TemplateSelectorInputs],
    generic.edit.CreateView,
):
    template_name = "stave/template_selector.html"
    form_class = forms.LeagueForm

    def get_context(self) -> contexts.TemplateSelectorInputs:
        return contexts.TemplateSelectorInputs(
            templates=models.LeagueTemplate.objects.all(),
            object_type="League",
            require_template_selection_first=False,
            selected_template=None,
        )

    def form_valid(self, form: forms.LeagueForm) -> HttpResponse:
        with transaction.atomic():
            if template_id := self.request.POST.get("template_id"):
                # We're cloning a league template.
                template = get_object_or_404(models.LeagueTemplate, pk=template_id)
                league = template.clone(**form.cleaned_data)
            else:
                league = form.save()

            # Make the current user a league manager
            _ = models.LeagueUserPermission.objects.create(
                league=league,
                user=self.request.user,
                permission=models.UserPermission.LEAGUE_MANAGER,
            )

            # Make the current user an event manager
            _ = models.LeagueUserPermission.objects.create(
                league=league,
                user=self.request.user,
                permission=models.UserPermission.EVENT_MANAGER,
            )
            self.object = league

            return HttpResponseRedirect(self.get_success_url())


class LeagueDetailView(
    TypedContextMixin[contexts.LeagueDetailViewInputs], generic.DetailView
):
    template_name = "stave/league_detail.html"
    model = models.League

    def get_queryset(self) -> QuerySet[models.League]:
        return models.League.objects.visible(self.request.user)

    def get_context(self) -> contexts.LeagueDetailViewInputs:
        return contexts.LeagueDetailViewInputs(
            events=self.get_object().events.listed(self.request.user)
        )


class LeagueListView(generic.ListView):
    template_name = "stave/league_list.html"
    model = models.League

    def get_queryset(self) -> QuerySet[models.League]:
        return models.League.objects.visible(self.request.user)


class EventListView(generic.ListView):
    template_name = "stave/event_list.html"
    model = models.Event

    def get_queryset(self) -> QuerySet[models.Event]:
        return models.Event.objects.visible(self.request.user)


class FormCreateUpdateView(LoginRequiredMixin, views.View):
    def get(
        self,
        request: HttpRequest,
        league_slug: str,
        event_slug: str,
        form_slug: str | None = None,
    ) -> HttpResponse:
        event = get_object_or_404(
            models.Event.objects.manageable(request.user),
            league__slug=league_slug,
            slug=event_slug,
        )

        form = None
        question_queryset = models.Question.objects.none()
        if form_slug:
            form = get_object_or_404(
                models.ApplicationForm.objects.manageable(request.user),
                slug=form_slug,
                event__slug=event_slug,
                event__league__slug=league_slug,
            )
            question_queryset = form.form_questions.all()

        app_form_form = forms.ApplicationFormForm(event=event, instance=form)
        question_formset = forms.QuestionFormSet(queryset=question_queryset)

        return render(
            request,
            "stave/form_edit.html",
            context={
                "form": app_form_form,
                "event": event,
                "question_formset": question_formset,
                "QuestionKind": models.QuestionKind,
                "url_base": request.path,
            },
        )

    def post(
        self,
        request: HttpRequest,
        league_slug: str,
        event_slug: str,
        form_slug: str | None = None,
        kind: models.QuestionKind | None = None,
    ) -> HttpResponse:
        # TODO: status
        event: models.Event = get_object_or_404(
            models.Event.objects.manageable(request.user),
            league__slug=league_slug,
            slug=event_slug,
        )

        form: models.ApplicationForm | None = None
        question_queryset = models.Question.objects.none()
        url_base = reverse("form-create", args=[league_slug, event_slug])
        if form_slug:
            form: models.ApplicationForm = get_object_or_404(
                models.ApplicationForm.objects.manageable(request.user),
                slug=form_slug,
                event__slug=event_slug,
                event__league__slug=league_slug,
            )
            question_queryset = form.form_questions.all()
            url_base = reverse("form-update", args=[league_slug, event_slug, form_slug])

        app_form_form = forms.ApplicationFormForm(
            event=event, data=request.POST, instance=form
        )
        question_formset = forms.QuestionFormSet(
            request.POST, queryset=question_queryset
        )

        if kind:
            # The user asked to add a question.
            if kind in models.QuestionKind.values:
                new_data = question_formset.data.copy()
                try:
                    count = int(new_data["form-TOTAL_FORMS"])
                    new_data[f"form-{count}-id"] = ""
                    new_data[f"form-{count}-kind"] = str(kind)
                    new_data[f"form-{count}-options"] = "[]"

                    count += 1
                    new_data["form-TOTAL_FORMS"] = str(count)
                except (KeyError, ValueError):
                    return HttpResponseBadRequest("invalid question data")

                question_formset = forms.QuestionFormSet(
                    data=new_data, queryset=question_queryset
                )
                # TODO: make the question forms not have errors when they're first created.
        elif app_form_form.is_valid() and question_formset.is_valid():
            # We did a save action, _without_ adding a question.
            app_form_form.save()
            # Commit the forms.
            with transaction.atomic():
                app_form_form.instance.event = event
                app_form = app_form_form.save()

                index = 0
                for question_form in question_formset.forms:
                    question_form.instance.application_form = app_form
                    if not question_form.cleaned_data.get(
                        "DELETE",
                        False,  # should import this TODO
                    ):
                        question_form.instance.order_key = index
                        index += 1

                question_formset.save_existing_objects()
                question_formset.save_new_objects()

            return HttpResponseRedirect(app_form.get_absolute_url())

        # We either did a question add, or we had invalid forms. Re-render.
        return render(
            request,
            "stave/form_edit.html",
            context={
                "form": app_form_form,
                "event": event,
                "question_formset": question_formset,
                "QuestionKind": models.QuestionKind,
                "url_base": url_base,
            },
        )


class ProfileView(
    LoginRequiredMixin,
    generic.edit.UpdateView,
):
    template_name = "stave/profile.html"
    model = models.User
    fields = models.User.ALLOWED_PROFILE_FIELDS
    success_url = reverse_lazy("profile")

    def get_object(self) -> models.User:
        return self.request.user


class SingleApplicationView(
    LoginRequiredMixin,
    TypedContextMixin[contexts.ViewApplicationContext],
    generic.DetailView,
):
    template_name = "stave/view_application.html"
    model = models.Application

    def get_queryset(self) -> QuerySet[models.Application]:
        return models.Application.objects.visible(self.request.user)

    def get_context(self) -> contexts.ViewApplicationContext:
        application: models.Application = self.get_object()
        return contexts.ViewApplicationContext(
            ApplicationStatus=models.ApplicationStatus,
            application=application,
            form=application.form,
            profile_form=None,
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


class FormApplicationsView(
    LoginRequiredMixin,
    TypedContextMixin[contexts.FormApplicationsInputs],
    generic.ListView,
):
    template_name = "stave/form_applications.html"
    model = models.Application

    def get_context(self) -> contexts.FormApplicationsInputs:
        form = get_object_or_404(
            models.ApplicationForm,
            slug=self.kwargs["application_form_slug"],
            event__slug=self.kwargs["event_slug"],
            event__league__slug=self.kwargs["league_slug"],
        )
        applications = {
            key: list(group)
            for key, group in itertools.groupby(
                self.get_queryset().order_by("status"), lambda i: i.status
            )
        }
        return contexts.FormApplicationsInputs(
            form=form,
            applications=applications,
            ApplicationStatus=models.ApplicationStatus,
            invited_unsent_count=len(
                [
                    a
                    for a in applications[models.ApplicationStatus.INVITED]
                    if not a.invitation_email_sent
                ],
            ),
        )

    def get_queryset(self) -> QuerySet[models.Application]:
        form = get_object_or_404(
            models.ApplicationForm.objects.manageable(self.request.user),
            slug=self.kwargs["application_form_slug"],
            event__slug=self.kwargs["event_slug"],
            event__league__slug=self.kwargs["league_slug"],
        )
        return models.Application.objects.visible(self.request.user).filter(form=form)


class ApplicationStatusView(LoginRequiredMixin, views.View):
    def post(
        self, request: HttpRequest, pk: UUID, status: models.ApplicationStatus
    ) -> HttpResponse:
        application: models.Application = get_object_or_404(
            models.Application.objects.visible(request.user),
            pk=pk,
        )

        # There are different legal state transformations based on whether the actor
        # is the applicant or the event manager.
        is_this_user = request.user == application.user
        legal_changes = [
            not is_this_user
            and application.status == models.ApplicationStatus.APPLIED
            and status
            in [
                models.ApplicationStatus.INVITED,
                models.ApplicationStatus.CONFIRMED,
                models.ApplicationStatus.REJECTED,
            ],
            application.status in [models.ApplicationStatus.INVITED]
            and status
            in [models.ApplicationStatus.CONFIRMED, models.ApplicationStatus.DECLINED],
            application.status
            in [models.ApplicationStatus.APPLIED, models.ApplicationStatus.CONFIRMED]
            and status == models.ApplicationStatus.WITHDRAWN,
        ]

        if any(legal_changes):
            application.status = status
            application.save()
            redirect_url = request.POST.get("redirect_url")
            if redirect_url and url_has_allowed_host_and_scheme(
                redirect_url, settings.ALLOWED_HOSTS
            ):
                return HttpResponseRedirect(redirect_url)

        else:
            return HttpResponseBadRequest(f"invalid status {status}")

        return HttpResponseRedirect("/")


class SetGameCrewView(LoginRequiredMixin, views.View):
    def post(
        self,
        request: HttpRequest,
        league_slug: str,
        event_slug: str,
        form_slug: str,
        game_id: UUID,
        role_group_id: UUID,
        crew_id: UUID | None = None,
    ) -> HttpResponse:
        game: models.Game = get_object_or_404(
            models.Game.objects.manageable(request.user),
            pk=game_id,
        )
        rgca: models.RoleGroupCrewAssignment = get_object_or_404(
            game.role_groups, role_group_id=role_group_id
        )
        if crew_id:
            crew = get_object_or_404(
                models.Crew.objects.filter(
                    event=game.event, kind=models.CrewKind.GAME_CREW
                ),
                pk=crew_id,
            )
        else:
            crew = None

        rgca.crew = crew
        rgca.save()

        redirect_url = request.POST.get("redirect_url")
        if redirect_url and url_has_allowed_host_and_scheme(
            redirect_url, settings.ALLOWED_HOSTS
        ):
            return HttpResponseRedirect(redirect_url)
        else:
            return HttpResponseRedirect(game.event.get_absolute_url())


class CrewBuilderView(LoginRequiredMixin, views.View):
    def get(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
    ) -> HttpResponse:
        application_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
        )

        static_crews_by_role_group_id = defaultdict(list)
        for crew in application_form.static_crews():
            static_crews_by_role_group_id[crew.role_group_id].append(crew)

        event_crews_by_role_group_id = defaultdict(list)
        for crew in application_form.event_crews():
            event_crews_by_role_group_id[crew.role_group_id].append(crew)

        allow_static_crews_by_role_group_id = {
            role_group.id: (role_group.id not in event_crews_by_role_group_id)
            for role_group in application_form.role_groups.all()
        }
        any_static_crew_role_groups = any(allow_static_crews_by_role_group_id.values())

        return render(
            request,
            "stave/crew_builder.html",
            {
                "request": request,
                "form": application_form,
                "static_crews": static_crews_by_role_group_id,
                "event_crews": event_crews_by_role_group_id,
                "allow_static_crews": allow_static_crews_by_role_group_id,
                "any_static_crew_role_groups": any_static_crew_role_groups,
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
        crew_id: UUID,
        role_id: UUID,
    ) -> HttpResponse:
        application_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
        )
        role = get_object_or_404(
            models.Role.objects.filter(
                role_group__in=application_form.role_groups.all()
            ),
            pk=role_id,
        )
        # We might have a Crew Id that's a game crew, a game override crew, an event crew, or a static crew.
        crew = get_object_or_404(
            models.Crew.objects.filter(
                event=application_form.event,
            ),
            pk=crew_id,
        )
        # TODO: verification
        context = crew.get_context()
        applications = list(application_form.get_applications_for_role(role, context))
        return render(
            request,
            "stave/crew_builder_detail.html",
            dataclasses.asdict(
                contexts.CrewBuilderDetailInputs(
                    form=application_form,
                    applications=applications,
                    game=context if isinstance(context, models.Game) else None,
                    event=application_form.event,
                    role=role,
                )
            ),
        )

    def post(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
        crew_id: UUID,
        role_id: UUID,
    ) -> HttpResponse:
        application_id = request.POST.get("application_id")
        if not application_id:
            return HttpResponseBadRequest("invalid application id")

        application_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
        )
        role = get_object_or_404(models.Role, pk=role_id)
        crew = get_object_or_404(models.Crew, pk=crew_id)
        # TODO: verification
        applications = application_form.applications.filter(
            id=application_id,
            roles__name=role.name,
        )
        if len(applications) != 1:
            return HttpResponseBadRequest("multiple matching applications")

        _ = models.CrewAssignment.objects.get_or_create(
            role=role,
            crew=crew,
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
            models.ApplicationForm.objects.accessible(request.user),
            slug=application_form,
            event__slug=event,
            event__league__slug=league,
        )
        if request.user.is_authenticated:
            existing_application = form.applications.filter(user=request.user).first()
            if existing_application:
                return HttpResponseRedirect(existing_application.get_absolute_url())

        if request.user.is_authenticated:
            profile_form_class = modelform_factory(
                models.User, fields=form.requires_profile_fields
            )
            profile_form = profile_form_class(
                instance=request.user,
                prefix="profile",
            )
        else:
            profile_form = None

        context = contexts.ViewApplicationContext(
            ApplicationStatus=models.ApplicationStatus,
            application=None,
            form=form,
            profile_form=profile_form,
            user_data={
                key: str(getattr(request.user, key))
                for key in form.requires_profile_fields
            }
            if request.user.is_authenticated
            else {},
            responses_by_id={},
            editable=request.user.is_authenticated
            and models.ApplicationForm.objects.submittable(request.user)
            .filter(id=form.id)
            .exists(),
        )

        return render(request, "stave/view_application.html", asdict(context))

    def post(
        self, request: HttpRequest, application_form: str, event: str, league: str
    ) -> HttpResponse:
        # TODO: if this is an edit to an existing application, replace data.
        app = None

        if not request.user.is_authenticated:
            return HttpResponseBadRequest("login first")  # TODO

        with transaction.atomic():
            form: models.ApplicationForm = get_object_or_404(
                models.ApplicationForm.objects.submittable(request.user),
                slug=application_form,
                event__slug=event,
                event__league__slug=league,
            )

            # Update the user Profile if needed
            profile_form_class = modelform_factory(
                models.User, fields=form.requires_profile_fields
            )
            profile_form = profile_form_class(
                instance=request.user, prefix="profile", data=request.POST
            )
            if not profile_form.is_valid():
                return HttpResponseBadRequest("bad profile")  # TODO

            profile_form.save()

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


class SendEmailView(LoginRequiredMixin, views.View):
    def get(
        self,
        request: HttpRequest,
        league_slug: str,
        event_slug: str,
        application_form_slug: str,
        email_type: str,
    ) -> HttpResponse:
        application_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            event__league__slug=league_slug,
            event__slug=event_slug,
            slug=application_form_slug,
        )

        try:
            email_type = models.SendEmailContextType(email_type)
        except ValueError:
            return HttpResponseBadRequest(f"invalid email_type {email_type}")

        initial = {}
        if message_template := application_form.get_template_for_context_type(
            email_type
        ):
            initial["content"] = message_template.content

        email_form = forms.SendEmailForm()

        return render(
            request,
            "stave/send_email.html",
            asdict(
                contexts.SendEmailInputs(
                    email_form=email_form,
                    kind=models.SendEmailContextType(email_type),
                    application_form=application_form,
                    members=application_form.get_user_queryset_for_context_type(
                        email_type
                    ),
                    redirect_url=request.GET.get("redirect_url"),
                )
            ),
        )

    def post(
        self,
        request: HttpRequest,
        league_slug: str,
        event_slug: str,
        application_form_slug: str,
        email_type: str,
    ) -> HttpResponse:
        application_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            event__league__slug=league_slug,
            event__slug=event_slug,
            slug=application_form_slug,
        )

        try:
            email_type = models.SendEmailContextType(email_type)
        except ValueError:
            return HttpResponseBadRequest(f"invalid email_type {email_type}")

        email_form = forms.SendEmailForm(data=request.POST)

        if email_form.is_valid():
            # Construct and render the template and persist a Message for each user.
            content: str = email_form.cleaned_data["content"]
            subject: str = email_form.cleaned_data["subject"]

            domain = "stave.app"  # FIXME: dynamic

            with transaction.atomic():
                for user in application_form.get_user_queryset_for_context_type(
                    email_type
                ):
                    application = application_form.applications.get(user=user)
                    # Substitute values for any of the user's tags.
                    # Note that the content will be sanitized when we
                    # render Markdown into HTML.
                    this_message_content = content.replace(
                        "{name}", user.preferred_name
                    )
                    this_message_content = this_message_content.replace(
                        "{schedule}", "TODO"
                    )

                    this_message_content = this_message_content.replace(
                        "{application}",
                        domain + application.get_absolute_url(),
                    )
                    this_message_content = this_message_content.replace(
                        "{event}",
                        domain + application_form.event.get_absolute_url(),
                    )

                    content_html = render_to_string(
                        "stave/email/invitation.html",
                        {"content": this_message_content, "domain": domain},
                    )
                    content_plain_text = render_to_string(
                        "stave/email/invitation.txt",
                        {"content": this_message_content, "domain": domain},
                    )

                    _ = models.Message.objects.create(
                        user=user,
                        subject=subject,
                        content_plain_text=content_plain_text,
                        content_html=content_html,
                    )
                    application.invitation_email_sent = True
                    application.save()

        messages.info(request, gettext_lazy("Your emails are being sent"))
        redirect_url = request.POST.get("redirect_url")
        if redirect_url and url_has_allowed_host_and_scheme(
            redirect_url, settings.ALLOWED_HOSTS
        ):
            return HttpResponseRedirect(redirect_url)

        return HttpResponseRedirect(application_form.event.get_absolute_url())
