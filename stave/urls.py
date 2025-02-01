from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('profile/', view=views.ProfileView.as_view(), name='profile'),
    path('leagues', view=views.LeagueListView.as_view(), name='league-list'),
    path('events', view=views.EventListView.as_view(), name='event-list'),
    path('_/<slug:slug>/', view=views.LeagueDetailView.as_view(), name='league-detail'),
    path('_/<slug:league>/<slug:slug>/', view=views.EventDetailView.as_view(), name="event-detail"),
    path('_/<slug:league>/<slug:application_form>/apply/', views.ApplicationFormView.as_view(), name="application-form"),
    path('_/<slug:league>/<slug:application_form>/applications/', views.FormApplicationsView.as_view(), name="form-applications"),
    path('my-applications', views.MyApplicationsView.as_view(), name="my-applications"),
    path('application/<uuid:pk>/', view=views.SingleApplicationView.as_view(), name='view-application'),

    # Crew Builder urls
    path('_/<slug:league>/<slug:application_form_slug>/builder/', views.CrewBuilderView.as_view(), name="crew-builder"),
    path('_/<slug:league>/<slug:application_form_slug>/builder/<uuid:pk>/', views.CrewBuilderDetailView.as_view(), name="crew-builder-detail"),

]
