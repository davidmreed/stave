from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("profile/", view=views.ProfileView.as_view(), name="profile"),
    path("events/", view=views.EventListView.as_view(), name="event-list"),
    path("events/create/", view=views.EventCreateView.as_view(), name="event-create"),
    path("leagues/", view=views.LeagueListView.as_view(), name="league-list"),
    path(
        "leagues/create/", view=views.LeagueCreateView.as_view(), name="league-create"
    ),
    path("_/<slug:slug>/", view=views.LeagueDetailView.as_view(), name="league-detail"),
    path(
        "_/<slug:slug>/edit/", view=views.LeagueUpdateView.as_view(), name="league-edit"
    ),
    path(
        "_/<slug:league>/<slug:event>/",
        view=views.EventDetailView.as_view(),
        name="event-detail",
    ),
    path(
        "_/<slug:league>/<slug:event>/edit",
        view=views.EventUpdateView.as_view(),
        name="event-edit",
    ),
    path(
        "_/<slug:league>/<slug:event>/create-form/<int:kind>",
        views.FormCreateView.as_view(),
        name="form-create-question",
    ),
    path(
        "_/<slug:league>/<slug:event>/create-form/",
        views.FormCreateView.as_view(),
        name="form-create",
    ),
    path(
        "_/<slug:league>/<slug:event>/<slug:application_form>/",
        views.ApplicationFormView.as_view(),
        name="application-form",
    ),
    path(
        "_/<slug:league_slug>/<slug:event_slug>/<slug:application_form_slug>/applications/",
        views.FormApplicationsView.as_view(),
        name="form-applications",
    ),
    path("my-applications", views.MyApplicationsView.as_view(), name="my-applications"),
    path(
        "application/<uuid:pk>/",
        view=views.SingleApplicationView.as_view(),
        name="view-application",
    ),
    path(
        "application/<uuid:pk>/<int:status>/",
        view=views.ApplicationStatusView.as_view(),
        name="application-status",
    ),
    # Crew Builder urls
    path(
        "_/<slug:league>/<slug:event_slug>/<slug:application_form_slug>/builder/",
        views.CrewBuilderView.as_view(),
        name="crew-builder",
    ),
    path(
        "_/<slug:league>/<slug:event_slug>/<slug:application_form_slug>/builder/<uuid:crew_id>/<uuid:role_id>/",
        views.CrewBuilderDetailView.as_view(),
        name="crew-builder-detail",
    ),
]
