import json

from django import forms
from django.utils.translation import gettext_lazy as _

from . import models


class SeparatedJSONListField(forms.JSONField):
    default_error_messages = {
        "invalid": _("Enter one or more choices separated by newlines.")
    }

    def prepare_value(self, value: list[str] | str) -> str:
        if isinstance(value, list):
            return "\n".join(value)

        return value

    def to_python(self, value: str) -> str:
        if value:
            python_value = [
                v.strip() for v in value.strip().replace("\r", "\n").split("\n") if v
            ]
        else:
            python_value = []

        return super().to_python(json.dumps(python_value))


class QuestionForm(forms.ModelForm):
    class Meta:
        model = models.Question
        fields = ["content", "kind", "required", "options", "allow_other"]
        widgets = {"kind": forms.HiddenInput(), "content": forms.TextInput}

    options = SeparatedJSONListField(
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text=_("Enter each option on a separate line"),
    )
    allow_other = forms.BooleanField(required=False)
    kind: models.QuestionKind

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)

        if self.instance:
            self.kind = self.instance.kind
        else:
            kind_data = kwargs.get("data", {}).get(kwargs["prefix"] + "-kind")
            if not kind_data:
                raise Exception("No kind specified for question")

            self.kind = models.QuestionKind(int(kind_data))

        match self.kind:
            case models.QuestionKind.SELECT_MANY:
                pass
            case models.QuestionKind.SELECT_ONE:
                self.fields["allow_other"].widget = forms.HiddenInput()
            case _:
                self.fields["options"].widget = forms.HiddenInput()
                self.fields["allow_other"].widget = forms.HiddenInput()

    def get_kind_display(self) -> str:
        match self.kind:
            case models.QuestionKind.SHORT_TEXT:
                return _("Short Text")
            case models.QuestionKind.LONG_TEXT:
                return _("Long Text")
            case models.QuestionKind.SELECT_ONE:
                return _("Select One Option")
            case models.QuestionKind.SELECT_MANY:
                return _("Select Multiple Options")


QuestionFormSet = forms.modelformset_factory(
    models.Question, form=QuestionForm, extra=0
)


class ApplicationFormForm(forms.ModelForm):
    application_kind = forms.TypedChoiceField(
        empty_value=None,
        choices=models.ApplicationKind,
        widget=forms.RadioSelect,
        help_text=models.ApplicationForm._meta.get_field("application_kind").help_text,
        required=True,
    )
    application_availability_kind = forms.TypedChoiceField(
        empty_value=None,
        choices=models.ApplicationAvailabilityKind,
        widget=forms.RadioSelect,
        help_text=models.ApplicationForm._meta.get_field(
            "application_availability_kind"
        ).help_text,
        required=True,
    )
    requires_profile_fields = forms.TypedMultipleChoiceField(
        empty_value=None,
        choices=[
            (field, models.User._meta.get_field(field).verbose_name.title())
            for field in models.User.ALLOWED_PROFILE_FIELDS
        ],
        widget=forms.CheckboxSelectMultiple,
        help_text=models.ApplicationForm._meta.get_field(
            "requires_profile_fields"
        ).help_text,
        required=False,
    )

    class Meta:
        model = models.ApplicationForm
        fields = [
            "slug",
            "role_groups",
            "application_kind",
            "application_availability_kind",
            "hidden",
            "intro_text",
        ]
        widgets = {"role_groups": forms.CheckboxSelectMultiple}

    def __init__(self, event: models.Event | None = None, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)
        if event:
            self.fields["role_groups"].queryset = event.role_groups.all()
        elif self.instance:
            self.fields["role_groups"].queryset = self.instance.role_groups.all()


class LeagueForm(forms.ModelForm):
    class Meta:
        model = models.League
        fields = ["name", "slug", "description", "logo", "website"]

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)


class CrewForm(forms.ModelForm):
    class Meta:
        model = models.Crew
        fields = ["name"]


class EventForm(forms.ModelForm):
    class Meta:
        model = models.Event
        fields = [
            "name",
            "slug",
            "status",
            "role_groups",
            "banner",
            "start_date",
            "end_date",
            "location",
        ]

    def __init__(self, *args, league: models.League | None = None, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)
        if league:
            self.fields["role_groups"].queryset = league.role_groups.all()
        elif self.instance:
            self.fields["role_groups"].queryset = self.instance.role_groups.all()


class EventFromTemplateForm(forms.ModelForm):
    class Meta:
        model = models.Event
        fields = [
            "name",
            "slug",
            "status",
            "banner",
            "start_date",
            "location",
        ]

    def __init__(self, *args, league: models.League, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)


class GameForm(forms.ModelForm):
    class Meta:
        model = models.Game
        fields = ["name", "order_key", "start_time", "end_time"]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = models.User.ALLOWED_PROFILE_FIELDS


class SendEmailForm(forms.Form):
    subject = forms.CharField(max_length=256)
    content = forms.CharField(max_length=2048, widget=forms.Textarea)  # TODO
