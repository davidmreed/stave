from django.contrib import admin
from django.urls import include, path

from . import calendars, settings, views

urlpatterns = [
    path(f"{settings.MEDIA_URL}<str:path>", view=views.MediaView.as_view()),
    path("", views.HomeView.as_view(), name="home"),
    path("about", views.AboutView.as_view(), name="about"),
    path("privacy", views.PrivacyPolicyView.as_view(), name="privacy-policy"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("profile/", view=views.ProfileView.as_view(), name="profile"),
    path("events/", view=views.EventListView.as_view(), name="event-list"),
    path("leagues/", view=views.LeagueListView.as_view(), name="league-list"),
    path(
        "leagues/create/", view=views.LeagueCreateView.as_view(), name="league-create"
    ),
    path("_/<slug:slug>/", view=views.LeagueDetailView.as_view(), name="league-detail"),
    path(
        "_/<slug:slug>/edit/", view=views.LeagueUpdateView.as_view(), name="league-edit"
    ),
    path(
        "_/<slug:league_slug>/create-event-with-template/",
        view=views.EventCreateView.as_view(),
        name="event-create",
    ),
    path(
        "_/<slug:league_slug>/create-event-with-template/<uuid:template_id>",
        view=views.EventCreateUpdateView.as_view(),
        name="event-create-template",
    ),
    path(
        "_/<slug:league>/events/<slug:event>/",
        view=views.EventDetailView.as_view(),
        name="event-detail",
    ),
    path(
        "_/<slug:league_slug>/create-event/",
        view=views.EventCreateUpdateView.as_view(),
        name="event-edit",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/edit/",
        view=views.EventCreateUpdateView.as_view(),
        name="event-edit",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/create-form/<int:kind>/",
        views.FormCreateUpdateView.as_view(),
        name="form-create-question",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:form_slug>/edit/",
        views.FormCreateUpdateView.as_view(),
        name="form-update",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:form_slug>/delete/",
        views.FormDeleteView.as_view(),
        name="form-delete",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:form_slug>/edit/<int:kind>/",
        views.FormCreateUpdateView.as_view(),
        name="form-update-question",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/create-form/",
        views.FormCreateUpdateView.as_view(),
        name="form-create",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:application_form_slug>/",
        views.ApplicationFormView.as_view(),
        name="application-form",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:application_form_slug>/applications/",
        views.FormApplicationsView.as_view(),
        name="form-applications",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:application_form_slug>/email/<str:email_type>/",
        views.SendEmailView.as_view(),
        name="send-email",
    ),
    path("my-applications", views.MyApplicationsView.as_view(), name="my-applications"),
    path(
        "application/<uuid:pk>/",
        view=views.SingleApplicationView.as_view(),
        name="view-application",
    ),
    path(
        "application/<uuid:pk>/edit/",
        view=views.SingleApplicationView.as_view(),
        name="update-application",
    ),
    path(
        "application/<uuid:pk>/<int:status>/",
        view=views.ApplicationStatusView.as_view(),
        name="application-status",
    ),
    path(
        "officiating-history",
        views.OfficiatingHistoryView.as_view(),
        name="officiating-history",
    ),
    # Crew Builder urls
    path(
        "_/<slug:league>/events/<slug:event_slug>/forms/<slug:application_form_slug>/builder/",
        views.CrewBuilderView.as_view(),
        name="crew-builder",
    ),
    path(
        "_/<slug:league>/events/<slug:event_slug>/forms/<slug:application_form_slug>/builder/<uuid:crew_id>/<uuid:role_id>/",
        views.CrewBuilderDetailView.as_view(),
        name="crew-builder-detail",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:form_slug>/builder/add-crew/",
        views.CrewCreateView.as_view(),
        name="crew-builder-add-crew",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:form_slug>/builder/set-crew/<uuid:game_id>/<uuid:role_group_id>/",
        views.SetGameCrewView.as_view(),
        name="set-game-crew",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/forms/<slug:form_slug>/builder/set-crew/<uuid:game_id>/<uuid:role_group_id>/<uuid:crew_id>/",
        views.SetGameCrewView.as_view(),
        name="set-game-crew",
    ),
    # Schedule URLs
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/schedule/",
        views.ScheduleView.as_view(),
        name="event-schedule",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/schedule/user/<uuid:user_id>/",
        views.ScheduleView.as_view(),
        name="event-user-schedule",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/schedule/role-groups/<str:role_group_ids>",
        views.ScheduleView.as_view(),
        name="event-role-group-schedule",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/schedule/user/<uuid:user_id>/role-groups/<str:role_group_ids>",
        views.ScheduleView.as_view(),
        name="event-user-role-group-schedule",
    ),
    path(
        "_/<slug:league_slug>/events/<slug:event_slug>/staff-list/",
        views.StaffedUserView.as_view(),
        name="event-staff-list",
    ),
    # Calendars
    path(
        "_/<slug:league_slug>/calendar/",
        calendars.LeagueEventsFeed(),
        name="calendar-league",
    ),
    path("calendar/", calendars.AllEventsFeed(), name="calendar-all"),
    path(
        "calendar/user/<uuid:user_id>", calendars.MyEventsFeed(), name="calendar-user"
    ),
]
