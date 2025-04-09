import dataclasses
import itertools
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django import views
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
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
            events = models.Event.objects.manageable(self.request.user)
        else:
            applications = []
            events = []

        context["application_forms"] = application_forms
        context["events"] = events
        context["applications"] = applications

        return context


class AboutView(generic.TemplateView):
    template_name = "stave/about.html"


class PrivacyPolicyView(generic.TemplateView):
    template_name = "stave/privacy.html"


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
        return (
            models.Event.objects.filter(league__slug=self.kwargs["league"])
            .visible(user=self.request.user)
            .prefetch_for_display()
        )


class ParentChildCreateUpdateFormView(views.View, ABC):
    template_name: str = "stave/parent_child_create_update.html"
    form_class: type[forms.ParentChildForm]

    @abstractmethod
    def get_object(self, request: HttpRequest, **kwargs) -> Any | None: ...

    @abstractmethod
    def get_view_url(self) -> str: ...

    def get_form(self, **kwargs) -> forms.ParentChildForm:
        return self.form_class(**kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        object_ = self.get_object(request, **kwargs)
        form = self.get_form(instance=object_)

        # On a GET, we can process adds but not deletes.
        if request.GET.get("action") == "add":
            form.add_child_form()

        return render(
            request,
            template_name=self.template_name,
            context={
                "object": object_,
                "form": form,
                "view_url": self.get_view_url(),
                "parent_name": self.form_class.parent_form_class._meta.model._meta.verbose_name,
                "child_name": self.form_class.child_form_class._meta.model._meta.verbose_name,
                "child_name_plural": self.form_class.child_form_class._meta.model._meta.verbose_name_plural,
            },
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        object_ = self.get_object(request, **kwargs)
        form = self.get_form(instance=object_, data=request.POST)

        action = request.GET.get("action")
        match action:
            case "add":
                # We requested to add a child object.
                form.add_child_form()
            case "delete":
                # We requested to delete a child object.
                index = request.GET.get("index")
                if index:
                    try:
                        index = int(index)
                        # Index validation is done by the form.
                        form.delete_child_form(index)
                    except ValueError:
                        pass
            case _:
                if form.is_valid():
                    object_ = form.save()
                    return HttpResponseRedirect(object_.get_absolute_url())
        return render(
            request,
            template_name=self.template_name,
            context={
                "object": object_,
                "form": form,
                "view_url": self.get_view_url(),
                "parent_name": self.form_class.parent_form_class._meta.model._meta.verbose_name,
                "child_name": self.form_class.child_form_class._meta.model._meta.verbose_name,
                "child_name_plural": self.form_class.child_form_class._meta.model._meta.verbose_name_plural,
            },
        )


class EventCreateUpdateView(LoginRequiredMixin, ParentChildCreateUpdateFormView):
    form_class = forms.EventCreateUpdateForm

    def get_form(self, **kwargs) -> forms.EventCreateUpdateForm:
        league = get_object_or_404(
            models.League.objects.manageable(self.request.user),
            slug=self.kwargs.get("league_slug"),
        )
        return forms.EventCreateUpdateForm(league=league, **kwargs)

    def get_object(
        self,
        request: HttpRequest,
        league_slug: str | None = None,
        event_slug: str | None = None,
        **kwargs,
    ) -> models.Event | None:
        if league_slug and event_slug:
            return get_object_or_404(
                models.Event.objects.manageable(request.user)
                .prefetch_for_display()
                .filter(
                    league__slug=league_slug,
                ),
                slug=event_slug,
            )

    def get_view_url(self) -> str:
        league_slug = self.kwargs.get("league_slug")
        event_slug = self.kwargs.get("event_slug")

        if league_slug and event_slug:
            return reverse("event-edit", args=[league_slug, event_slug])
        elif league_slug:
            return reverse("event-edit", args=[league_slug])

        return ""  # FIXME: raise appropriate exception


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
            slug=self.kwargs.get("league_slug"),
        )
        self.selected_template = None

        if template_id := request.POST.get("template_id"):
            # template_id being present means the first form, the selector, was submitted.
            if template_id != "none":
                # "none" is the sigil for "select no template"
                self.selected_template = get_object_or_404(
                    self.league.event_templates.all(), pk=template_id
                )

    def get_form_class(self) -> type:
        return forms.EventFromTemplateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["league"] = self.league

        # If we're just moving to the second screen, we don't want
        # to validate the form yet (since the user hasn't had a chance
        # to do any entry).

        if "slug" not in self.request.POST and "data" in kwargs:
            # This form submission wasn't from a page that had the form rendered.
            # (i.e., the template selector screen)
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

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not self.league.event_templates.exists():
            # No templates. Redirect to the template-free create page.
            return HttpResponseRedirect(reverse("event-edit", args=[self.league.slug]))

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if "slug" in self.request.POST:
            # This submission was of the clone-from-selected-template form.
            # Let Django process the form for us.
            return super().post(request, *args, **kwargs)
        else:
            if self.selected_template:
                self.object = None
                return self.render_to_response(self.get_context_data())
            else:
                # The user doesn't want to clone a template
                # Redirect them to the Create Event form.
                return HttpResponseRedirect(
                    reverse("event-edit", args=[self.league.slug])
                )

    def form_valid(self, form: forms.EventFromTemplateForm) -> HttpResponse:
        with transaction.atomic():
            # We're cloning an event template.
            event = self.selected_template.clone(**form.cleaned_data)
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
            template_id = self.request.POST.get("template_id")
            if template_id and template_id != "none":
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
                event.forms.manageable(request.user),
                slug=form_slug,
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
    generic.edit.UpdateView,
):
    template_name = "stave/view_application.html"
    model = models.Application
    form_class = forms.ApplicationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        application = self.get_object()
        kwargs.update(
            {
                "instance": application,
                "editable": self.request.path.endswith("/edit/"),
                "label_suffix": "",
                "user": application.user,
                "app_form": application.form,
            }
        )

        return kwargs

    def get_queryset(self) -> QuerySet[models.Application]:
        return models.Application.objects.visible(
            self.request.user
        ).prefetch_for_display()

    def get_context(self) -> contexts.ViewApplicationContext:
        application: models.Application = self.get_object()
        application_form = self.get_form()
        # Force a clean since we're going to override
        # the `form` kwarg from our mixin
        _ = application_form.is_valid()

        return contexts.ViewApplicationContext(
            ApplicationStatus=models.ApplicationStatus,
            application=application,
            app_form=application.form,
            form=application_form,
            editable=self.request.path.endswith("/edit/"),
        )

    def form_valid(self, form: forms.ApplicationForm):
        self.object = form.save()
        return super().form_valid(form)


class FormApplicationsView(
    LoginRequiredMixin,
    TypedContextMixin[contexts.FormApplicationsInputs],
    generic.TemplateView,
):
    template_name = "stave/form_applications.html"
    model = models.Application

    def get_context(self) -> contexts.FormApplicationsInputs:
        form: models.ApplicationForm | None = (
            models.ApplicationForm.objects.manageable(self.request.user)
            .prefetch_applications()
            .filter(
                slug=self.kwargs["application_form_slug"],
                event__slug=self.kwargs["event_slug"],
                event__league__slug=self.kwargs["league_slug"],
            )
            .first()
        )

        if not form:
            raise Http404()

        applications = {
            key: list(group)
            for key, group in itertools.groupby(
                sorted(form.applications.all(), key=lambda a: a.status),
                lambda a: a.status,
            )
        }
        return contexts.FormApplicationsInputs(
            form=form,
            applications=applications,
            ApplicationStatus=models.ApplicationStatus,
            invited_unsent_count=len(
                [
                    a
                    for a in applications.get(models.ApplicationStatus.INVITED, [])
                    if not a.invitation_email_sent
                ],
            ),
        )


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
        is_this_user = request.user.id == application.user_id
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


class ScheduleView(LoginRequiredMixin, views.View):
    def get(
        self,
        request: HttpRequest,
        league_slug: str,
        event_slug: str,
        role_group_ids: str | None = None,
        user_id: UUID | None = None,
    ) -> HttpResponse:
        # Determine what type of schedule is requested, and whether the user
        # has permission to view that schedule.

        # Must be a user staffed on the event to view, or a manager.
        event: models.Event = get_object_or_404(
            models.Event.objects.all(),
            slug=event_slug,
            league__slug=league_slug,
        )  # TODO: prefetch

        manageable = (
            models.Event.objects.filter(id=event.id).manageable(request.user).exists()
        )
        staffed = (
            models.User.objects.filter(
                id__in=models.CrewAssignment.objects.filter(
                    crew__event=event,
                ).values("user_id")
            )
            .distinct()
            .filter(id=request.user.id)
            .exists()
        )

        if not manageable and not staffed:
            return HttpResponseForbidden()

        role_groups = event.role_groups.all()
        if role_group_ids:
            role_groups = role_groups.filter(id__in=role_group_ids.split(","))

        games = event.games.filter(role_groups__role_group__in=role_groups).distinct()

        static_crews_by_role_group_id = defaultdict(list)
        for crew in event.static_crews().prefetch_assignments():
            static_crews_by_role_group_id[crew.role_group_id].append(crew)

        event_crews_by_role_group_id = defaultdict(list)
        for crew in event.event_crews().prefetch_assignments():
            event_crews_by_role_group_id[crew.role_group_id].append(crew)

        allow_static_crews_by_role_group_id = {
            role_group.id: (role_group.id not in event_crews_by_role_group_id)
            for role_group in event.role_groups.all()
        }
        any_static_crew_role_groups = any(allow_static_crews_by_role_group_id.values())

        return render(
            request,
            "stave/crew_builder.html",
            context=asdict(
                contexts.CrewBuilderInputs(
                    editable=False,
                    form=None,
                    event=event,
                    role_groups=role_groups,
                    games=games,
                    focus_user_id=user_id,
                    static_crews=static_crews_by_role_group_id,
                    event_crews=event_crews_by_role_group_id,
                    allow_static_crews=allow_static_crews_by_role_group_id,
                    any_static_crew_role_groups=any_static_crew_role_groups,
                )
            ),
        )


class CrewBuilderView(LoginRequiredMixin, views.View):
    def get(
        self,
        request: HttpRequest,
        league: str,
        event_slug: str,
        application_form_slug: str,
    ) -> HttpResponse:
        application_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user)
            .prefetch_applications()
            .prefetch_crews(),
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
            context=asdict(
                contexts.CrewBuilderInputs(
                    editable=True,
                    form=application_form,
                    event=application_form.event,
                    role_groups=application_form.role_groups.all(),
                    games=application_form.games(),
                    focus_user_id=None,
                    static_crews=static_crews_by_role_group_id,
                    event_crews=event_crews_by_role_group_id,
                    allow_static_crews=allow_static_crews_by_role_group_id,
                    any_static_crew_role_groups=any_static_crew_role_groups,
                )
            ),
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
            models.ApplicationForm.objects.manageable(
                request.user
            ).prefetch_applications(),
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

        # If there's already a user assigned, we want to replace them in the
        # target role.
        assignment = models.CrewAssignment.objects.filter(
            role=role,
            crew=crew,
        ).first()

        if assignment:
            assignment.user = applications[0].user
            assignment.save()
        else:
            _ = models.CrewAssignment.objects.create(
                role=role, crew=crew, user=applications[0].user
            )

        # Redirect the user to the base Crew Builder for this crew
        return HttpResponseRedirect(
            reverse("crew-builder", args=[league, event_slug, application_form_slug])
        )


class ApplicationFormView(views.View):
    def get(
        self,
        request: HttpRequest,
        application_form_slug: str,
        event_slug: str,
        league_slug: str,
    ) -> HttpResponse:
        app_form = get_object_or_404(
            models.ApplicationForm.objects.accessible(request.user),
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league_slug,
        )
        if request.user.is_authenticated:
            existing_application = app_form.applications.filter(
                user=request.user
            ).first()
            if existing_application:
                return HttpResponseRedirect(existing_application.get_absolute_url())
        editable = (
            request.user.is_authenticated
            and models.ApplicationForm.objects.submittable(request.user)
            .filter(id=app_form.id)
            .exists()
        )
        form = forms.ApplicationForm(
            app_form,
            request.user if request.user.is_authenticated else None,
            instance=None,
            editable=editable,
            label_suffix="",
        )

        context = contexts.ViewApplicationContext(
            ApplicationStatus=models.ApplicationStatus,
            application=None,
            form=form,
            app_form=app_form,
            editable=editable,
        )

        return render(request, "stave/view_application.html", asdict(context))

    def post(
        self,
        request: HttpRequest,
        application_form_slug: str,
        event_slug: str,
        league_slug: str,
    ) -> HttpResponse:
        app = None

        if not request.user.is_authenticated:
            return HttpResponseBadRequest("login first")  # TODO

        app_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.submittable(request.user),
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league_slug,
        )
        form = forms.ApplicationForm(
            app_form,
            request.user,
            data=request.POST,
            instance=None,
            editable=True,
            label_suffix="",
        )
        if form.is_valid():
            app = form.save()
            return HttpResponseRedirect(reverse("view-application", args=[app.id]))

        context = contexts.ViewApplicationContext(
            ApplicationStatus=models.ApplicationStatus,
            application=None,
            app_form=app_form,
            form=form,
            editable=request.user.is_authenticated
            and models.ApplicationForm.objects.submittable(request.user)
            .filter(id=app_form.id)
            .exists(),
        )

        return render(request, "stave/view_application.html", asdict(context))


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

            domain = "https://stave.app"  # FIXME: dynamic

            with transaction.atomic():
                for user in application_form.get_user_queryset_for_context_type(
                    email_type
                ):
                    application = application_form.applications.get(user=user)
                    # Substitute values for any of the user's tags.
                    # Note that the content will be sanitized when we
                    # render Markdown into HTML.
                    # TODO: we should sanitize the strings first and substitute after rendering.
                    this_message_content = content.replace(
                        "{name}", user.preferred_name
                    )
                    this_message_content = this_message_content.replace(
                        "{schedule}",
                        "`"
                        + domain
                        + reverse(
                            "event-user-role-group-schedule",
                            args=[
                                application_form.event.league.slug,
                                application_form.event.slug,
                                user.id,
                                ",".join(
                                    str(rg.id)
                                    for rg in application_form.role_groups.all()
                                ),
                            ],
                        )
                        + "`",
                    )

                    this_message_content = this_message_content.replace(
                        "{application}",
                        "`" + domain + application.get_absolute_url() + "`",
                    )
                    this_message_content = this_message_content.replace(
                        "{event}",
                        "`" + domain + application_form.event.get_absolute_url() + "`",
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
