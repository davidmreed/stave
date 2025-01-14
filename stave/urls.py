from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('<slug:league>/<slug:application_form>/apply/', views.application_form, name="application-form")
]
