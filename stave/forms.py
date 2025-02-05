from django import forms
from . import models
from django.http import HttpRequest


class ApplicationFormForm(forms.ModelForm):
    class Meta:
        model = models.ApplicationForm
        fields = [
            "event",
            "slug",
            "role_groups",
            "application_kind",
            "application_availability_kind",
            "hidden",
            "intro_text",
            "requires_profile_fields",
        ]


class LeagueForm(forms.ModelForm):
    class Meta:
        model = models.League
        fields = ["name", "slug", "description", "logo", "website"]


class EventForm(forms.ModelForm):
    league = forms.ModelChoiceField(queryset=None)

    class Meta:
        model = models.Event
        fields = [
            "league",
            "role_groups",
            "name",
            "slug",
            "banner",
            "start_date",
            "end_date",
            "location",
        ]

    def __init__(self, *args, **kwargs):
        request: HttpRequest = kwargs.pop("request")
        super().__init__(*args, **kwargs)

        self.fields["league"].queryset = models.League.objects.filter(
            user_permissions__permission=models.UserPermission.LEAGUE_MANAGER,
            user_permissions__user=request.user,
        )
        self.fields["league"].initial = self.fields["league"].queryset.first()
