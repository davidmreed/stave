from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from . import models

def application_form(request: HttpRequest, league: str, application_form: str) -> HttpResponse:
    if request.method == 'GET':
        league = get_object_or_404(models.League, slug=league)
        form = get_object_or_404(models.ApplicationForm, slug=application_form, event__league=league)

        return render(request, "stave/application_form.html", {"form": form})
    elif request.method == 'POST':
        user_input = request.POST
        #with transaction.atomic():
        league = get_object_or_404(models.League, slug=league)
        form = get_object_or_404(models.ApplicationForm, slug=application_form, event__league=league)

        print(request.POST)

        # Construct and persist an Application, ApplicationResponse, and RoleAssignments

        app = models.Application(form=form, user=request.user, status=models.ApplicationStatus.APPLIED)

        # Pull out Availability information
        if form.application_availability_kind == models.ApplicationAvailabilityKind.BY_DAY:
            app.availability = [
                f"day-{day}" in request.POST
                for day in form.event.days()
            ]
        elif form.application_availability_kind == models.ApplicationAvailabilityKind.BY_GAME:
            app.availability = [
                f"game-{game.id}" in request.POST
                for game in form.event.games.all()
            ]

        app.save()

        # Pull out Roles
        for role_group in form.role_groups.all():
            for role in role_group.roles.all():
                if f"role-{role.id}" in request.POST:
                    role_assignment = models.RoleAssignment(
                        role = role,
                        user = request.user,
                        status = models.ApplicationStatus.APPLIED,
                        application = app
                    )
                    role_assignment.save()


        # Question answers
        for question in form.form_questions.all():
            if str(question.id) in request.POST:
                values = request.POST.getlist(str(question.id))
                if not values or (
                    len(values) != 1 and question.kind != question.QuestionKind.SELECT_MANY
                    ):
                    return HttpResponse(400)
                if question.kind in (models.QuestionKind.SHORT_TEXT, models.QuestionKind.LONG_TEXT):
                    content = values[0]
                else:
                    # The content of `values` should be indices into the `options` array
                    # for this question
                    try:
                        answers = [question.options[int(v)] for v in values]
                    except (ValueError, IndexError):
                        return HttpResponse(400)

                    if f"{question.id}-other" in request.POST:
                        if not question.allow_other or not request.POST.get(f"{question.id}-other-value"):
                            return HttpResponse("bad other")
                        else:
                            answers.append(request.POST[f"{question.id}-other-value"])

                    content=(answers if len(answers) > 1 else answers[0])

                if question.required and not content:
                    return HttpResponse("Missing content")

                response = models.ApplicationResponse(
                    application=app,
                    question=question,
                    content=content
                )
                response.save()
            else:
                return HttpResponse(f"missing question {question.content}")

        return HttpResponseRedirect(reverse("home"))

    return HttpResponse(405)
