from django.shortcuts import render, get_object_or_404

from django.http import HttpRequest, HttpResponse

from . import models

def application_form(request: HttpRequest, league: str, application_form: str) -> HttpResponse:
    league = get_object_or_404(models.League, slug=league)
    form = get_object_or_404(models.ApplicationForm, slug=application_form, event__league=league)

    return render(request, "stave/application_form.html", {"form": form})
