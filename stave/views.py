from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import is_dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID
from zoneinfo import ZoneInfo

from django import views
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import (
    FileResponse,
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import slugify
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_date
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.utils.translation import gettext, gettext_lazy
from django.views import generic
from django.forms.formsets import DELETION_FIELD_NAME
from meta.views import Meta

from stave.templates.stave import contexts

from . import forms, models, settings
from .avail import AvailabilityManager, ScheduleManager

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


class TypedContextMixin[T: dict[str, Any] | DataclassInstance]:
    def get_context(self) -> T: ...

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)

        typed_context = self.get_context()
        if is_dataclass(typed_context):
            context.update(contexts.to_dict(typed_context))
        else:
            context.update(typed_context)

        return context


class TenantedObjectMixin:
    league: models.League

    def setup(self, request: HttpRequest, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.league = get_object_or_404(
            models.League.objects.manageable(self.request.user),
            slug=self.kwargs.get("league_slug"),
        )

    def get_context_data(self, *args, **kwargs) -> dict:
        base = super().get_context_data(*args, **kwargs)

        base["league"] = self.league

        return base


class TenantedGenericDeleteView[T](
    LoginRequiredMixin, TenantedObjectMixin, generic.edit.DeleteView
):
    template_name = "stave/confirm_delete.html"
    list_view_name: str

    def get_object(self) -> T:
        return get_object_or_404(
            self.model.objects.filter(league=self.league),
            id=self.kwargs.get("id"),
        )

    def get_success_url(self) -> str:
        return reverse(self.list_view_name, args=[self.league.slug])


class MediaView(views.View):
    # TODO: do not serve files unless associated with a viewable
    # league or application form.

    def get(self, request: HttpRequest, path: str) -> HttpResponse:
        file_path = Path(settings.MEDIA_ROOT) / path

        if file_path.exists():
            return FileResponse(file_path.open("rb"))

        return HttpResponseNotFound()


class MyApplicationsView(LoginRequiredMixin, generic.ListView):
    template_name = "stave/my_applications.html"
    model = models.Application

    def get_queryset(self) -> QuerySet[models.Application]:
        return (
            super()
            .get_queryset()
            .filter(user=self.request.user)
            .order_by("-form__event__start_date")
        )


class OfficiatingHistoryView(LoginRequiredMixin, generic.ListView):
    """
    A view that displays a user's officiating history.

    The QuerySet fetches all RoleGroupCrewAssignments with a crew that has the user in a crew
    assignment. `get_context_data` then computes the effective crew for each of those and bulids a
    list of GameHistory's. This requires only a single query, and a bit of filtering in memory.

    The QuerySet can be paginated, although the number of game histories shown on the results could
    be less than the size of the page because the effective crew may not include the user, and could
    even theoretically be empty. This could be fixed by having get_queryset return GameHistory's,
    but it's not clear if that can be composed as a QuerySet.
    """

    template_name = "stave/officiating_history.html"
    model = models.RoleGroupCrewAssignment

    def get_queryset(self):
        cas = models.CrewAssignment.objects.filter(user=self.request.user)
        crews = models.Crew.objects.filter(
            assignments__in=cas, event__status=models.EventStatus.COMPLETE
        )
        rgcas = models.RoleGroupCrewAssignment.objects.filter(
            Q(crew__in=crews) | Q(crew_overrides__in=crews)
        ).order_by("-game__start_time")
        return rgcas

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        histories = []
        for rgca in context["object_list"]:
            cas = [ca for ca in rgca.effective_crew() if ca.user == self.request.user]
            # A user can have up to two roles in a game. Primary role is the one with
            # `nonexclusive=True`.
            if len(cas) == 0:
                continue
            elif len(cas) == 1:
                role = cas[0].role
                secondary_role = None
            else:
                role = next((ca.role for ca in cas if ca.role.nonexclusive), None)
                assert role is not None
                secondary_role = next(
                    (ca.role for ca in cas if not ca.role.nonexclusive), None
                )
            history = models.GameHistory(
                game=rgca.game,
                user=self.request.user,
                role=role,
                secondary_role=secondary_role,
            )
            histories.append(history)
        context["histories"] = histories

        return context


class HomeView(generic.TemplateView):
    template_name = "stave/home.html"

    def get_context_data(self, *args, **kwargs):
        # TODO: switch to typed approach
        context = super().get_context_data(*args, **kwargs)

        application_forms = models.ApplicationForm.objects.listed(self.request.user)
        if self.request.user.is_authenticated:
            application_forms = application_forms.exclude(
                applications__user=self.request.user
            )
            applications = models.Application.objects.filter(
                user=self.request.user,
                form__event__start_date__gt=datetime.now(),
            ).exclude(status=models.ApplicationStatus.WITHDRAWN)
            events = models.Event.objects.manageable(self.request.user).exclude(
                status__in=[models.EventStatus.CANCELED, models.EventStatus.COMPLETE]
            )
        else:
            applications = []
            events = []

        context["application_forms"] = application_forms
        context["events"] = events
        context["applications"] = applications
        context["meta"] = Meta(
            site_name=gettext_lazy("Stave"),
            title=gettext_lazy("Stave: Signups and Staffing for Roller Derby"),
            description=gettext_lazy(
                "Build events and signup forms, manage officiating crews, and track your officiating calendar."
            ),
            url="https://stave.app",
            use_og=True,
        )

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

    def allow_child_deletes(self) -> bool:
        return True

    def get_time_zone(self) -> str | None:
        return None

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
            context=contexts.to_dict(
                contexts.ParentChildCreateUpdateInputs(
                    object=object_,
                    form=form,
                    parent_name=self.form_class.parent_form_class._meta.model._meta.verbose_name,
                    child_name=self.form_class.child_form_class._meta.model._meta.verbose_name,
                    child_name_plural=self.form_class.child_form_class._meta.model._meta.verbose_name_plural,
                    allow_child_deletes=self.allow_child_deletes(),
                    time_zone=self.get_time_zone(),
                )
            ),
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        object_ = self.get_object(request, **kwargs)
        form = self.get_form(instance=object_, data=request.POST, files=request.FILES)

        action = request.GET.get("action")
        match action:
            case "add":
                # We requested to add a child object.
                form.add_child_form()
            case "delete":
                # We requested to delete a child object.
                if self.allow_child_deletes():
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
                    return HttpResponseRedirect(form.get_redirect_url())

        return render(
            request,
            template_name=self.template_name,
            context=contexts.to_dict(
                contexts.ParentChildCreateUpdateInputs(
                    object=object_,
                    form=form,
                    parent_name=self.form_class.parent_form_class._meta.model._meta.verbose_name,
                    child_name=self.form_class.child_form_class._meta.model._meta.verbose_name,
                    child_name_plural=self.form_class.child_form_class._meta.model._meta.verbose_name_plural,
                    allow_child_deletes=self.allow_child_deletes(),
                    time_zone=self.get_time_zone(),
                )
            ),
        )


# League management views

## Message Templates


class MessageTemplateListView(
    LoginRequiredMixin, TenantedObjectMixin, generic.ListView
):
    template_name = "stave/message_template_list.html"
    model = models.MessageTemplate

    def get_queryset(self) -> QuerySet[models.MessageTemplate]:
        return self.league.message_templates.all()


class MessageTemplateCreateView(
    LoginRequiredMixin, TenantedObjectMixin, generic.edit.CreateView
):
    template_name = "stave/message_template_edit.html"
    form_class = forms.MessageTemplateForm

    def form_valid(self, form: forms.MessageTemplateForm) -> HttpResponse:
        form.instance.league = self.league
        self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("message-template-list", args=[self.league.slug])


class MessageTemplateUpdateView(
    LoginRequiredMixin, TenantedObjectMixin, generic.edit.UpdateView
):
    template_name = "stave/message_template_edit.html"
    form_class = forms.MessageTemplateForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["merge_fields"] = models.MergeContext(
            models.Application(),
            models.ApplicationForm(),
            models.Event(),
            models.League(),
            models.User(),
            models.User(),
        ).get_merge_fields()

        return context

    def get_object(
        self,
    ) -> models.MessageTemplate | None:
        return get_object_or_404(
            models.MessageTemplate.objects.filter(league=self.league),
            id=self.kwargs.get("message_template_id"),
        )

    def get_success_url(self) -> str:
        return reverse("message-template-list", args=[self.league.slug])


class MessageTemplateDeleteView(TenantedGenericDeleteView[models.MessageTemplate]):
    template_name = "stave/confirm_delete.html"
    list_view_name = "message-template-list"
    model = models.MessageTemplate


## Role Groups


class RoleGroupListView(LoginRequiredMixin, TenantedObjectMixin, generic.ListView):
    template_name = "stave/role_group_list.html"
    model = models.RoleGroup

    def get_queryset(self) -> QuerySet[models.RoleGroup]:
        return self.league.role_groups.all()


class RoleGroupCreateUpdateView(
    LoginRequiredMixin, TenantedObjectMixin, ParentChildCreateUpdateFormView
):
    form_class = forms.RoleGroupCreateUpdateForm
    role_group: models.RoleGroup | None

    def get_view_url(self) -> str:
        league_slug = self.kwargs.get("league_slug")
        role_group_id = self.kwargs.get("role_group_id")

        if role_group_id:
            return reverse("role-group-edit", args=[league_slug, role_group_id])
        else:
            return reverse("role-group-create", args=[league_slug])

    def get_form(self, **kwargs) -> forms.RoleGroupCreateUpdateForm:
        league = get_object_or_404(
            models.League.objects.manageable(self.request.user),
            slug=self.kwargs.get("league_slug"),
        )
        return forms.RoleGroupCreateUpdateForm(league=league, **kwargs)

    def get_object(
        self,
        request: HttpRequest,
        league_slug: str,
        role_group_id: UUID | None = None,
        **kwargs,
    ) -> models.RoleGroup | None:
        if role_group_id:
            self.role_group = get_object_or_404(
                self.league.role_groups.all(), id=role_group_id
            )
            return self.role_group

    def allow_child_deletes(self) -> bool:
        if self.role_group:
            return self.role_group.can_delete()
        return False


class RoleGroupDeleteView(TenantedGenericDeleteView[models.RoleGroup]):
    list_view_name = "role-group-list"
    model = models.RoleGroup

    def get_object(self) -> models.RoleGroup:
        role_group = super().get_object()
        if not role_group.can_delete():
            raise Exception(
                f"Cannot delete role group {role_group} because it is in use"
            )

        return role_group


## Event Templates


class EventTemplateListView(LoginRequiredMixin, TenantedObjectMixin, generic.ListView):
    template_name = "stave/event_template_list.html"
    model = models.EventTemplate

    def get_queryset(self) -> QuerySet[models.EventTemplate]:
        return self.league.event_templates.all()


class EventTemplateCreateUpdateView(
    LoginRequiredMixin, TenantedObjectMixin, ParentChildCreateUpdateFormView
):
    form_class = forms.EventTemplateCreateUpdateForm
    event_template: models.EventTemplate | None

    def get_view_url(self) -> str:
        league_slug = self.kwargs.get("league_slug")
        event_template_id = self.kwargs.get("event_group_id")

        if event_template_id:
            return reverse("event-template-edit", args=[league_slug, event_template_id])
        else:
            return reverse("event-template-create", args=[league_slug])

    def get_form(self, **kwargs) -> forms.EventTemplateCreateUpdateForm:
        return forms.EventTemplateCreateUpdateForm(league=self.league, **kwargs)

    def get_object(
        self,
        request: HttpRequest,
        league_slug: str,
        event_template_id: UUID | None = None,
        **kwargs,
    ) -> models.EventTemplate | None:
        if event_template_id:
            self.event_template = get_object_or_404(
                self.league.event_templates.all(), id=event_template_id
            )
            return self.event_template

    def allow_child_deletes(self) -> bool:
        return True


class EventTemplateDeleteView(TenantedGenericDeleteView[models.EventTemplate]):
    template_name = "stave/confirm_delete.html"
    model = models.EventTemplate
    list_view_name = "event-template-list"


## Application Form Templates


class ApplicationFormTemplateListView(
    LoginRequiredMixin, TenantedObjectMixin, generic.ListView
):
    template_name = "stave/application_form_template_list.html"
    model = models.ApplicationFormTemplate

    def get_queryset(self) -> QuerySet[models.ApplicationFormTemplate]:
        return self.league.application_form_templates.all()


class ApplicationFormTemplateCreateUpdateView(
    LoginRequiredMixin, TenantedObjectMixin, ParentChildCreateUpdateFormView
):
    form_class = forms.ApplicationFormTemplateCreateUpdateForm
    application_form_template: models.ApplicationFormTemplate | None

    def get_view_url(self) -> str:
        league_slug = self.kwargs.get("league_slug")
        id = self.kwargs.get("id")

        if id:
            return reverse("application-form-template-edit", args=[league_slug, id])
        else:
            return reverse("application-form-template-create", args=[league_slug])

    def get_form(self, **kwargs) -> forms.ApplicationFormTemplateCreateUpdateForm:
        return forms.ApplicationFormTemplateCreateUpdateForm(
            league=self.league, **kwargs
        )

    def get_object(
        self,
        request: HttpRequest,
        league_slug: str,
        id: UUID | None = None,
        **kwargs,
    ) -> models.ApplicationFormTemplate | None:
        if id:
            self.application_form_template = get_object_or_404(
                self.league.application_form_templates.all(), id=id
            )
            return self.application_form_template

    def allow_child_deletes(self) -> bool:
        return True


class ApplicationFormTemplateDeleteView(
    TenantedGenericDeleteView[models.ApplicationFormTemplate]
):
    template_name = "stave/confirm_delete.html"
    model = models.ApplicationFormTemplate
    list_view_name = "application-form-template-list"


# Non-Management Views


class EventCreateUpdateView(LoginRequiredMixin, ParentChildCreateUpdateFormView):
    form_class = forms.EventCreateUpdateForm

    def get_form(self, **kwargs) -> forms.EventCreateUpdateForm:
        league = get_object_or_404(
            models.League.objects.event_manageable(self.request.user),
            slug=self.kwargs.get("league_slug"),
        )

        if template_id := self.kwargs.get("template_id"):
            template = get_object_or_404(league.event_templates.all(), id=template_id)
            start_date = self.request.GET.get("start_date")
            try:
                if start_date:
                    start_date = parse_date(start_date)
            except ValueError:
                return HttpResponseBadRequest(f"invalid date {start_date}")

            name = self.request.GET.get("name") or template.name
            initial = {
                "name": name,
                "slug": slugify(name),
                "location": template.location,
                "role_groups": template.role_groups.all(),
                "start_date": start_date,
                "end_date": start_date + timedelta(days=template.days - 1)
                if start_date
                else None,
            }

            timezone = ZoneInfo(league.time_zone)
            game_template_initial = []
            for game_template in template.game_templates.all():
                game_template_initial.append(
                    {
                        "start_time": datetime.combine(
                            start_date + timedelta(days=game_template.day - 1),
                            game_template.start_time or time(12, 00),
                            tzinfo=timezone,
                        )
                        if start_date
                        else None,
                        "end_time": datetime.combine(
                            start_date + timedelta(days=game_template.day - 1),
                            game_template.end_time or time(14, 00),
                            tzinfo=timezone,
                        )
                        if start_date
                        else None,
                        "role_groups": game_template.role_groups.all(),
                        "home_league": game_template.home_league,
                        "visiting_league": game_template.visiting_league,
                        "home_team": game_template.home_team,
                        "visiting_team": game_template.visiting_team,
                        "association": game_template.association,
                        "kind": game_template.kind,
                    }
                )

        else:
            template = None
            initial = None
            game_template_initial = None

        return forms.EventCreateUpdateForm(
            league=league,
            parent_initial=initial,
            child_initial=game_template_initial,
            template=template,
            **kwargs,
        )

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

    def get_time_zone(self) -> str | None:
        league = get_object_or_404(
            models.League.objects.event_manageable(self.request.user),
            slug=self.kwargs.get("league_slug"),
        )
        return league.time_zone


class EventCreateView(
    LoginRequiredMixin,
    TypedContextMixin[contexts.TemplateSelectorInputs],
    generic.edit.CreateView,
):
    template_name = "stave/template_selector.html"
    league: models.League

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)

        self.league = get_object_or_404(
            models.League.objects.event_manageable(self.request.user),
            slug=self.kwargs.get("league_slug"),
        )

    def get_form_class(self) -> type:
        return forms.EventFromTemplateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["league"] = self.league

        return kwargs

    def get_context(self) -> contexts.TemplateSelectorInputs:
        return contexts.TemplateSelectorInputs(
            templates=self.league.event_templates.all(),
            object_type="Event",
            require_template_selection_first=False,
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not self.league.event_templates.exists():
            # No templates. Redirect to the template-free create page.
            return HttpResponseRedirect(reverse("event-edit", args=[self.league.slug]))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form: forms.EventFromTemplateForm) -> HttpResponse:
        template_id = self.request.POST.get("template_id")
        if template_id and template_id != "none":
            get_object_or_404(self.league.event_templates.all(), pk=template_id)
            url = reverse("event-create-template", args=[self.league.slug, template_id])
            querystring = urlencode(
                {"name": form.instance.name, "start_date": form.instance.start_date}
            )
            url = f"{url}?{querystring}"
        else:
            url = reverse("event-edit", args=[self.league.slug])

        return HttpResponseRedirect(url)


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

        models.Crew.objects.create(
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
            disclaimer=gettext_lazy(
                "To use Stave, you must agree not to use data you receive in applications "
                "for purposes that are not connected to the applicant's event participation "
                "or volunteer service. Misuse of data may result in your removal from the service. "
                "See the [Stave privacy policy](https://stave.app/privacy) for more details.\n\n"
                "**Click Create to indicate you accept these terms.**"
            ),
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
            models.LeagueUserPermission.objects.create(
                league=league,
                user=self.request.user,
                permission=models.UserPermission.LEAGUE_MANAGER,
            )

            # Make the current user an event manager
            models.LeagueUserPermission.objects.create(
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
        return models.Event.objects.listed(self.request.user)


class FormCreateUpdateView(LoginRequiredMixin, views.View):
    # TODO: add TypedContextMixin
    # TODO: use ParentChildCreateUpdateView
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
                event.application_forms.manageable(request.user),
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
                        DELETION_FIELD_NAME,
                        False,
                    ):
                        if question_form.instance.order_key != index:
                            question_form.instance.order_key = index
                            # force the formset to save this instance
                            question_form.has_changed = lambda: True
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


class FormDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    template_name = "stave/confirm_delete.html"
    model = models.ApplicationForm

    def get_object(self) -> models.ApplicationForm:
        return get_object_or_404(
            models.ApplicationForm.objects.manageable(self.request.user).filter(
                event__league__slug=self.kwargs.get("league_slug"),
                event__slug=self.kwargs.get("event_slug"),
            ),
            slug=self.kwargs.get("form_slug"),
        )

    def get_success_url(self) -> str:
        return (
            models.Event.objects.visible(self.request.user)
            .filter(
                league__slug=self.kwargs.get("league_slug"),
                slug=self.kwargs.get("event_slug"),
            )
            .first()
            .get_absolute_url()
        )


class FormOpenCloseView(LoginRequiredMixin, views.View):
    def post(
        self, request: HttpRequest, league_slug: str, event_slug: str, form_slug: str
    ) -> HttpResponse:
        form = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user).filter(
                event__league__slug=league_slug,
                event__slug=event_slug,
            ),
            slug=form_slug,
        )

        form.closed = request.path.endswith("/close/")
        form.save()

        redirect_url = request.POST.get("redirect_url")
        if redirect_url and url_has_allowed_host_and_scheme(
            redirect_url, settings.ALLOWED_HOSTS
        ):
            return HttpResponseRedirect(redirect_url)

        return HttpResponseRedirect(form.get_absolute_url())


class ProfileView(
    LoginRequiredMixin,
    generic.edit.UpdateView,
):
    template_name = "stave/profile.html"
    model = models.User
    fields = [f for f in models.User.ALLOWED_PROFILE_FIELDS if f != "email"]
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
        application_form.is_valid()

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

        return contexts.FormApplicationsInputs(
            form=form,
            applications_action=form.applications.open(),
            applications_inprogress=form.applications.in_progress(),
            applications_staffed=form.applications.staffed(),
            applications_closed=form.applications.closed(),
            ApplicationStatus=models.ApplicationStatus,
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
        legal_changes = application.get_legal_state_changes(request.user)

        if status in legal_changes:
            application.status = status

            # If the application status changed to Confirmed,
            # and the user is already staffed, move it to Assignment Pending.
            # TODO: move this logic into the Application
            if (
                status == models.ApplicationStatus.CONFIRMED
                and application.form.application_kind
                == models.ApplicationKind.CONFIRM_THEN_ASSIGN
                and application.has_assignments()
            ):
                application.status = models.ApplicationStatus.ASSIGNMENT_PENDING
            elif status == models.ApplicationStatus.DECLINED:
                # Delete any assignments that were already made
                models.CrewAssignment.objects.filter(
                    user=application.user,
                    crew__event=application.form.event,
                    role__in=application.roles.all(),
                ).delete()

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
            game.role_group_crew_assignments.all(), role_group_id=role_group_id
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


class CrewDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    template_name = "stave/confirm_delete.html"
    model = models.Crew

    def get_object(self) -> models.Crew:
        return get_object_or_404(
            models.Crew.objects.filter(
                id=self.kwargs.get("crew_id"),
                kind=models.CrewKind.GAME_CREW,
                event__in=models.Event.objects.manageable(self.request.user),
            ),
        )

    def get_success_url(self) -> str:
        redirect_url = self.request.GET.get("redirect_url")
        if redirect_url and url_has_allowed_host_and_scheme(
            redirect_url, settings.ALLOWED_HOSTS
        ):
            return redirect_url

        return self.get_object().event.get_absolute_url()


class StaffedUserView(LoginRequiredMixin, views.View):
    def get(
        self,
        request: HttpRequest,
        league_slug: str,
        event_slug: str,
    ) -> HttpResponse:
        event: models.Event = get_object_or_404(
            models.Event.objects.manageable(request.user),
            slug=event_slug,
            league__slug=league_slug,
        )  # TODO: prefetch

        staffed = models.User.objects.staffed(event)

        return render(
            request,
            "stave/staff_list.html",
            context=contexts.to_dict(
                contexts.StaffListInputs(users=staffed, event=event)
            ),
        )


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
        )

        manageable = (
            models.Event.objects.filter(id=event.id).manageable(request.user).exists()
        )
        staffed = models.User.objects.staffed(event).filter(id=request.user.id).exists()
        if not manageable and not staffed:
            return HttpResponseForbidden()

        # Crew Builder requires that all Override Crews be present on our RoleGroupCrewAssignments.
        with transaction.atomic():
            role_groups = event.role_groups.all()
            if role_group_ids:
                role_groups = role_groups.filter(id__in=role_group_ids.split(","))

            for rgca in models.RoleGroupCrewAssignment.objects.filter(
                role_group__in=role_groups,
                game__event=event,
            ).select_for_update():
                if not rgca.crew_overrides_id:
                    rgca.crew_overrides = models.Crew.objects.create(
                        kind=models.CrewKind.OVERRIDE_CREW,
                        role_group_id=rgca.role_group_id,
                        event_id=event.id,
                    )
                    rgca.save()

        sm = ScheduleManager(event, role_groups)

        static_crews_by_role_group_id = defaultdict(list)
        for crew in sm.static_crews:
            static_crews_by_role_group_id[crew.role_group_id].append(crew)

        event_crews_by_role_group_id = defaultdict(list)
        for crew in sm.event_crews:
            event_crews_by_role_group_id[crew.role_group_id].append(crew)

        counts = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for crew in sm.event.crews.all():
            for role in crew.role_group.roles.all():
                counts[crew.role_group.id][crew.id][role.name] = (0, 0)

        return render(
            request,
            "stave/crew_builder.html",
            context=contexts.to_dict(
                contexts.CrewBuilderInputs(
                    editable=False,
                    form=None,
                    event=sm.event,
                    role_groups=sm.event.role_groups.all(),
                    games=sm.event.games.all(),
                    focus_user_id=user_id,
                    static_crews=static_crews_by_role_group_id,
                    event_crews=event_crews_by_role_group_id,
                    allow_static_crews=False,
                    counts=counts,
                    show_day_header=(
                        len(sm.event.games.all()) and len(sm.event.days())
                    ),
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
        application_form_check: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            slug=application_form_slug,
            event__slug=event_slug,
            event__league__slug=league,
        )

        # Crew Builder requires that all Override Crews be present on our RoleGroupCrewAssignments.
        with transaction.atomic():
            for rgca in models.RoleGroupCrewAssignment.objects.filter(
                role_group__in=application_form_check.role_groups.all(),
                game__event=application_form_check.event,
            ).select_for_update():
                if not rgca.crew_overrides_id:
                    rgca.crew_overrides = models.Crew.objects.create(
                        kind=models.CrewKind.OVERRIDE_CREW,
                        role_group_id=rgca.role_group_id,
                        event_id=application_form_check.event_id,
                    )
                    rgca.save()

        # For all of the crew editor elements we render (one per game per role group,
        # and one per static crew), we need to be able to answer the question
        # "How many total apps are there for each role, and how many of those apps
        # are actually available?"

        # This is a fairly complicated data problem, so we're going to pre-compute
        # everything here.
        # After this point, all data access should be via `am` to use prefetched data.
        am = AvailabilityManager.with_application_form(application_form_check)

        static_crews_by_role_group_id = defaultdict(list)
        for crew in am.static_crews:
            static_crews_by_role_group_id[crew.role_group_id].append(crew)

        event_crews_by_role_group_id = defaultdict(list)
        for crew in am.event_crews:
            event_crews_by_role_group_id[crew.role_group_id].append(crew)

        override_crews_to_games = {}
        for game in am.application_form.event.games.all():
            for rgca in game.role_group_crew_assignments.all():
                if rgca.role_group in am.application_form.role_groups.all():
                    override_crews_to_games[rgca.crew_overrides] = game

        allow_static_crews = len(am.application_form.event.games.all()) > 1 and any(
            not role_group.event_only
            for role_group in am.application_form.role_groups.all()
        )
        show_day_header = len(am.application_form.event.games.all()) and len(
            am.application_form.event.days()
        )
        counts = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        # The contexts we're interested in are all of the static crews,
        # event crews, and per-game override crews.
        all_crews = (
            am.static_crews + am.event_crews + list(override_crews_to_games.keys())
        )

        for crew in all_crews:
            for role in crew.role_group.roles.all():
                counts[crew.role_group.id][crew.id][role.name] = (
                    am.get_application_counts(
                        crew, override_crews_to_games.get(crew), role
                    )
                )

        return render(
            request,
            "stave/crew_builder.html",
            context=contexts.to_dict(
                contexts.CrewBuilderInputs(
                    editable=True,
                    form=am.application_form,
                    event=am.application_form.event,
                    role_groups=am.application_form.role_groups.all(),
                    games=am.application_form.event.games.all(),
                    focus_user_id=None,
                    static_crews=static_crews_by_role_group_id,
                    event_crews=event_crews_by_role_group_id,
                    allow_static_crews=allow_static_crews,
                    counts=counts,
                    show_day_header=show_day_header,
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
            role_group=role.role_group,
        )
        # TODO: this is not maximally efficient (filter by role)
        am = AvailabilityManager.with_application_form(application_form)
        if crew.kind == models.CrewKind.OVERRIDE_CREW:
            game = crew.get_context()
        else:
            game = None
        applications = am.get_available_applications(crew, game, role)

        # TODO: get the Game from AM to reduce queries.
        return render(
            request,
            "stave/crew_builder_detail.html",
            contexts.to_dict(
                contexts.CrewBuilderDetailInputs(
                    form=application_form,
                    applications=applications,
                    game=game,
                    event=am.application_form.event,
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
        crew = get_object_or_404(
            application_form.event.crews.filter(role_group=role.role_group), pk=crew_id
        )

        if application_id:
            applications = application_form.applications.filter(
                id=application_id,
                roles__name=role.name,
            ).exclude(status=models.ApplicationStatus.WITHDRAWN)
            if len(applications) != 1:
                return HttpResponseBadRequest("invalid application_id")
        else:
            applications = []

        # Delete existing assignment, if present
        if assignment := models.CrewAssignment.objects.filter(
            role=role,
            crew=crew,
        ).first():
            # Delete the assignment
            assignment.delete()

            # Find the application corresponding to the existing assignment.
            existing_application = (
                application_form.applications.filter(
                    user=assignment.user, roles__name=role.name
                )
                .exclude(status=models.ApplicationStatus.WITHDRAWN)
                .first()
            )
            # There should be exactly one.
            if existing_application and not existing_application.has_assignments():
                # Reset its status appropriately.
                if (
                    existing_application.status
                    == models.ApplicationStatus.ASSIGNMENT_PENDING
                ):
                    if (
                        application_form.application_kind
                        == models.ApplicationKind.CONFIRM_THEN_ASSIGN
                    ):
                        existing_application.status = models.ApplicationStatus.CONFIRMED
                    else:
                        existing_application.status = models.ApplicationStatus.APPLIED
                elif (
                    existing_application.status
                    == models.ApplicationStatus.INVITATION_PENDING
                ):
                    existing_application.status = models.ApplicationStatus.APPLIED
                existing_application.save()

        # Add a new assignment, if requested
        if applications:
            models.CrewAssignment.objects.create(
                role=role, crew=crew, user=applications[0].user
            )

            # Update the status of the application
            if (
                applications[0].form.application_kind
                == models.ApplicationKind.ASSIGN_ONLY
            ):
                # Note that this sends apps in ASSIGNED status backwards,
                # so they'll get an update email.
                applications[0].status = models.ApplicationStatus.ASSIGNMENT_PENDING
            else:
                # for CONFIRM_THEN_ASSIGN events, our status update depends on the current status as well.
                match applications[0].status:
                    case models.ApplicationStatus.APPLIED:
                        applications[
                            0
                        ].status = models.ApplicationStatus.INVITATION_PENDING
                    case models.ApplicationStatus.CONFIRMED:
                        applications[
                            0
                        ].status = models.ApplicationStatus.ASSIGNMENT_PENDING
                    case _:
                        # All other cases do not update.
                        pass

            applications[0].save()

        # Redirect the user to the base Crew Builder for this crew
        context = crew.get_context()
        if isinstance(context, models.Game):
            fragment = context.id
        else:
            fragment = crew.id

        return HttpResponseRedirect(
            reverse("crew-builder", args=[league, event_slug, application_form_slug])
            + f"#ctx-{fragment}"
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
            # If the user has an existing non-withdrawn application, redirect them to it.
            existing_application = (
                app_form.applications.filter(
                    user=request.user,
                )
                .exclude(status=models.ApplicationStatus.WITHDRAWN)
                .first()
            )
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
        meta = Meta(
            site_name=gettext_lazy("Stave"),
            title=gettext_lazy("Apply for {} at {}").format(
                app_form.event.name, app_form.event.league.name
            ),
            description=app_form.intro_text,
            url=request.path,
            use_og=True,
        )
        if app_form.event.banner:
            meta.image_object = {"url": app_form.event.banner.url}
        elif app_form.event.league.logo:
            meta.image_object = {"url": app_form.event.league.logo.url}

        return render(
            request,
            "stave/view_application.html",
            {"meta": meta, **contexts.to_dict(context)},
        )

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
        existing_application = (
            app_form.applications.filter(
                user=request.user,
            )
            .exclude(status=models.ApplicationStatus.WITHDRAWN)
            .first()
        )

        if existing_application:
            # Show the user a message and redirect them to their existing application
            messages.info(
                request,
                gettext_lazy(
                    "You've already applied to this event. Edit your existing application instead."
                ),
            )
            return HttpResponseRedirect(existing_application.get_absolute_url())

        form = forms.ApplicationForm(
            app_form,
            request.user,
            data=request.POST,
            instance=None,
            editable=True,
            label_suffix="",
        )

        if form.is_valid():
            from . import emails  # avoid circular import

            app = form.save()
            # Send the user an acknowledgement email.
            context = models.MergeContext(
                app, app_form, app_form.event, app_form.event.league, request.user, None
            )
            emails.send_message(
                app,
                None,
                None,
                gettext("Your application to {event.name}"),
                gettext(
                    "We received your application to [{event.name}]({event.link}). "
                    "You can manage your [application]({application.link}) on Stave. "
                    "You'll receive an email when the {event.name} organizers update "
                    "your application.\n\n"
                    "Please don't reply to this message. It is not monitored.\n\n"
                    "Thank you for your application!"
                ),
            )

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

        return render(request, "stave/view_application.html", contexts.to_dict(context))


class CommCenterView(LoginRequiredMixin, views.View):
    def get(
        self,
        request: HttpRequest,
        league_slug: str,
        event_slug: str,
        application_form_slug: str,
    ) -> HttpResponse:
        application_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            event__league__slug=league_slug,
            event__slug=event_slug,
            slug=application_form_slug,
        )

        pending_invitation = application_form.applications.filter(
            status=models.ApplicationStatus.INVITATION_PENDING
        )
        pending_rejection = application_form.applications.filter(
            status=models.ApplicationStatus.REJECTION_PENDING
        )
        pending_assignment = application_form.applications.filter(
            status=models.ApplicationStatus.ASSIGNMENT_PENDING
        )

        return render(
            request,
            "stave/comms.html",
            contexts.to_dict(
                contexts.CommCenterInputs(
                    pending_invitation=pending_invitation,
                    pending_rejection=pending_rejection,
                    pending_assignment=pending_assignment,
                    application_form=application_form,
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
    ) -> HttpResponse:
        """Send templated emails to the whole relevant population,
        using the configured template."""
        application_form: models.ApplicationForm = get_object_or_404(
            models.ApplicationForm.objects.manageable(request.user),
            event__league__slug=league_slug,
            event__slug=event_slug,
            slug=application_form_slug,
        )

        try:
            email_type = models.SendEmailContextType(request.POST.get("type"))
        except ValueError:
            return HttpResponseBadRequest(f"invalid email_type {email_type}")

        member_queryset = application_form.get_user_queryset_for_context_type(
            email_type
        )

        # A specific user was intended as the target
        if recipient := request.POST.get("recipient"):
            member_queryset = member_queryset.filter(id=recipient)

        if not member_queryset.exists():
            messages.error(request, gettext_lazy("No recipients were selected"))
            return HttpResponseRedirect(request.path)

        from . import emails

        for member in member_queryset:
            # TODO: bulkify
            application = (
                application_form.applications.filter(user=member)
                .exclude(status=models.ApplicationStatus.WITHDRAWN)
                .first()
            )
            emails.send_message_from_messagetemplate(
                application, request.user, email_type
            )

        messages.info(request, gettext_lazy("Your emails are being sent"))
        redirect_url = request.POST.get("redirect_url")
        if redirect_url and url_has_allowed_host_and_scheme(
            redirect_url, settings.ALLOWED_HOSTS
        ):
            return HttpResponseRedirect(redirect_url)

        return HttpResponseRedirect(application_form.event.get_absolute_url())


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

        member_queryset = application_form.get_user_queryset_for_context_type(
            email_type
        )

        merge_context = models.MergeContext(
            league=application_form.event.league,
            event=application_form.event,
            app_form=application_form,
            application=models.Application(),
            # We don't have an actual user yet;
            # this context is just to get the merge field names.
            user=request.user,
            sender=request.user,
        )

        # If we have a GET param with a user id in it, filter down to that.
        # (Supplying the applicant query if we do not have a member_queryset or email_type)
        if target_member := request.GET.get("recipient"):
            if member_queryset is None:
                member_queryset = models.User.objects.filter(
                    id__in=application_form.applications.all().values("user_id")
                ).distinct()

            member_queryset = member_queryset.filter(id=target_member)

        initial = {}
        if member_queryset.count() == 1:
            # Set the `user` value on the merge_context
            merge_context.user = member_queryset.first()

        if message_template := application_form.get_template_for_context_type(
            email_type
        ):
            from . import emails

            if member_queryset.count() == 1:
                initial["subject"] = emails.substitute(
                    merge_context, message_template.subject
                )
                initial["content"] = emails.substitute(
                    merge_context, message_template.content
                )
            else:
                initial["subject"] = message_template.subject
                initial["content"] = message_template.content

        email_form = forms.SendEmailForm(initial=initial)
        email_recipients_form = forms.SendEmailRecipientsForm(
            member_queryset,
            initial={"recipients": member_queryset},
        )

        return render(
            request,
            "stave/send_email.html",
            contexts.to_dict(
                contexts.SendEmailInputs(
                    email_form=email_form,
                    email_recipients_form=email_recipients_form,
                    kind=models.SendEmailContextType(email_type),
                    application_form=application_form,
                    merge_fields=merge_context.get_merge_fields(),
                    redirect_url=request.GET.get("redirect_url"),
                    recipient_count=member_queryset.count(),
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
        email_recipients_form = forms.SendEmailRecipientsForm(
            application_form.get_user_queryset_for_context_type(email_type),
            data=request.POST,
        )

        if email_form.is_valid() and email_recipients_form.is_valid():
            # Construct and render the template and persist a Message for each user.
            content: str = email_form.cleaned_data["content"]
            subject: str = email_form.cleaned_data["subject"]
            with transaction.atomic():
                from . import emails  # avoid circular import

                recipients = email_recipients_form.cleaned_data["recipients"]
                if not recipients:
                    messages.error(request, gettext_lazy("No recipients were selected"))
                for user in recipients:
                    application = (
                        application_form.applications.filter(user=user)
                        .exclude(status=models.ApplicationStatus.WITHDRAWN)
                        .first()
                    )
                    emails.send_message(
                        application, request.user, email_type, subject, content
                    )

                if recipients:
                    messages.info(request, gettext_lazy("Your emails are being sent"))
            redirect_url = request.POST.get("redirect_url")
            if redirect_url and url_has_allowed_host_and_scheme(
                redirect_url, settings.ALLOWED_HOSTS
            ):
                return HttpResponseRedirect(redirect_url)

        # Reconstructing the original context to allow us to render the form
        # with errors is kind of gnarly - just redirect back to Send Email.
        return HttpResponseRedirect(request.path)
