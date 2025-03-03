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
from typing import Any, TYPE_CHECKING
from collections.abc import Mapping
import itertools
from uuid import UUID
from . import models, settings, forms
from stave.templates.stave import contexts
from dataclasses import dataclass, asdict, is_dataclass
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime
import dataclasses
from django.utils.translation import gettext_lazy

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


class MyApplicationsView(LoginRequiredMixin, generic.ListView):
    template_name = "stave/my_applications.html"
    model = models.Application

    def get_queryset(self) -> QuerySet[models.Application]:
        return super().get_queryset().filter(user=self.request.user)


class HomeView(generic.TemplateView):
    template_name = "stave/home.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        application_forms = models.ApplicationForm.objects.open()
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


class CrewCreateView(LoginRequiredMixin, views.View):
    def post(self, request: HttpRequest, league_slug: str, event_slug: str, form_slug: str) -> HttpResponse:
        form = get_object_or_404(models.ApplicationForm.objects.filter(
            event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
            event__league__user_permissions__user=self.request.user).distinct(),
            event__league__slug=league_slug,
            event__slug=event_slug,
            slug = form_slug
        )
        role_group = get_object_or_404(
                form.role_groups.all(),
                pk = request.POST.get("role_group_id")
            )

        name = gettext_lazy("{} Crew {}").format(
                role_group,
                models.Crew.objects.filter(event=form.event, kind=models.CrewKind.GAME_CREW, role_group=role_group).count() + 1
        )

        _ = models.Crew.objects.create(
            kind = models.CrewKind.GAME_CREW,
            event = form.event,
            role_group = role_group,
            name = name,
        )
        redirect_url = request.POST.get("redirect_url")
        if redirect_url and url_has_allowed_host_and_scheme(
                redirect_url, settings.ALLOWED_HOSTS
        ):
            return HttpResponseRedirect(redirect_url)

        return HttpResponseRedirect(form.get_absolute_url())

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


class FormCreateView(LoginRequiredMixin, views.View):
    def get(self, request: HttpRequest, league: str, event: str) -> HttpResponse:
        event_ = get_object_or_404(
            models.Event.objects.filter(
                league__slug=league,
                league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
                league__user_permissions__user=request.user,
            ).distinct(),
            slug=event,
        )
        app_form_form = forms.ApplicationFormForm()
        question_formset = forms.QuestionFormSet(
            queryset=models.Question.objects.none()
        )

        return render(
            request,
            "stave/form_edit.html",
            context={
                "form": app_form_form,
                "event": event_,
                "question_formset": question_formset,
                "QuestionKind": models.QuestionKind,
            },
        )

    def post(
        self, request: HttpRequest, league: str, event: str, **kwargs
    ) -> HttpResponse:
        event_ = get_object_or_404(
            models.Event.objects.filter(
                league__slug=league,
                league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
                league__user_permissions__user=request.user,
            ).distinct(),
            slug=event,
        )

        app_form_form = forms.ApplicationFormForm(request.POST)
        question_formset = forms.QuestionFormSet(request.POST)

        # TODO: implement Save and Continue
        # Determine if the user took a form-wide action, like Save or Save and Continue,
        # or if they asked to add a question.
        if (
            "kind" not in kwargs
            and app_form_form.is_valid()
            and question_formset.is_valid()
        ):
            with transaction.atomic():
                app_form = app_form_form.save(commit=False)
                app_form.event = event_
                app_form.role_groups.set(
                    models.RoleGroup.objects.filter(
                        id__in=app_form_form.cleaned_data["role_groups"]
                    )
                )
                print(app_form)
                app_form.save()

                for i, instance in enumerate(question_formset.save(commit=False)):
                    instance.application_form = app_form
                    instance.order_key = i
                    instance.save()

            return HttpResponseRedirect(app_form.get_absolute_url())
        elif "kind" in kwargs:
            kind: int = kwargs["kind"]
            if kind in models.QuestionKind.values:
                new_data = question_formset.data.copy()
                try:
                    count = int(new_data["form-TOTAL_FORMS"])
                    new_data[f"form-{count}-id"] = ""
                    new_data[f"form-{count}-kind"] = str(kind)
                    if kind in [
                        models.QuestionKind.SELECT_ONE,
                        models.QuestionKind.SELECT_MANY,
                    ]:
                        new_data[f"form-{count}-options"] = "[]"

                    count += 1
                    new_data["form-TOTAL_FORMS"] = str(count)
                except (KeyError, ValueError):
                    return HttpResponseBadRequest()

                question_formset = forms.QuestionFormSet(data=new_data)
            else:
                return HttpResponseBadRequest()

        return render(
            request,
            "stave/form_edit.html",
            context={
                "form": app_form_form,
                "event": event_,
                "question_formset": question_formset,
                "QuestionKind": models.QuestionKind,
            },
        )


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
    ApplicationStatus: type
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
        ).distinct()

    def get_context(self) -> ViewApplicationContext:
        application: models.Application = self.get_object()
        return ViewApplicationContext(
            ApplicationStatus=models.ApplicationStatus,
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
            models.Application.objects.filter(
            Q(user=request.user) | Q(
                form__event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
                form__event__league__user_permissions__user=self.request.user,
                )).distinct(), pk=pk)

        # There are different legal state transformations based on whether the actor
        # is the applicant or the event manager.
        is_this_user = request.user == application.user
        legal_changes = [
            not is_this_user
            and application.status == models.ApplicationStatus.APPLIED
            and status in [models.ApplicationStatus.INVITED, models.ApplicationStatus.CONFIRMED, models.ApplicationStatus.REJECTED],
            application.status in [models.ApplicationStatus.INVITED] and status in [models.ApplicationStatus.CONFIRMED, models.ApplicationStatus.DECLINED],
            application.status in [models.ApplicationStatus.APPLIED, models.ApplicationStatus.CONFIRMED] and status == models.ApplicationStatus.WITHDRAWN,
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

        return render(
            request,
            "stave/crew_builder.html",
            {
                "form": application_form,
                "static_crews": application_form.static_crews(),
                "event_crews_by_role_group_id": {}, # TODO
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
        application_form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
            event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
            event__league__user_permissions__user=self.request.user,
        )
        role = get_object_or_404(models.Role.objects.filter(role_group__in=application_form.role_groups.all()), pk=role_id)
        # We might have a Crew Id that's a game crew, a game override crew, an event crew, or a static crew.
        crew = get_object_or_404(
            models.Crew.objects.filter(
                event=application_form.event,
            ),
            pk=crew_id
        )
        # TODO: verification
        context = crew.get_context()
        applications = list(application_form.get_applications_for_role(
            role, context
        ))
        return render(
            request,
            "stave/crew_builder_detail.html",
            dataclasses.asdict(contexts.CrewBuilderDetailInputs(
                    form=application_form,
                    applications=applications,
                    game=context if isinstance(context, models.Game) else None,
                    event=application_form.event,
                    role=role,
                )),
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

        application_form = get_object_or_404(
            models.ApplicationForm,
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
            event__league__user_permissions__permission=models.UserPermission.EVENT_MANAGER,
            event__league__user_permissions__user=self.request.user,
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
            role_id=role_id,
            crew_id=crew_id,
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
            ApplicationStatus=models.ApplicationStatus,
            application=None,
            form=form,
            user_data={
                key: str(
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
        # TODO: enforce authentication
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
