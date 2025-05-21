import copy
import json

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.utils import ErrorDict
from django.utils import timezone
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


class MultipleChoiceOrOtherWidget(forms.MultiWidget):
    def get_context(self, name, value, attrs):
        # This is a goofy hack to get around the fact that MultiWidget
        # doesn't handle the situation where our compound value is itself a sequence.
        value = {"values": value}

        return super().get_context(name, value, attrs)

    def decompress(
        self, value: dict[str, list[str]]
    ) -> tuple[list[str], str] | tuple[list[str]]:
        values: tuple[list[str], str] = ([], "")
        if value and value.get("values"):
            value = value["values"]
            # When we're redisplaying a form with errors, we get back our already-decompresssed data structure
            if isinstance(value[0], list):
                return value

            # Otherwise, decompress an actual flat list of values
            legal_values = [c[0] for c in self.widgets[0].choices]
            multi_choice_values = [v for v in value if v in legal_values]
            other = [v for v in value if v not in legal_values]
            if other:
                multi_choice_values += ["other"]
            values = (multi_choice_values, ",".join(other))

        return values[: len(self.widgets)]


class MultipleChoiceOrOtherField(forms.MultiValueField):
    allow_other: bool

    def __init__(self, choices, allow_other: bool, *args, **kwargs):
        self.allow_other = allow_other

        if allow_other:
            choices = choices + [("other", _("Other"))]
            fields = (
                forms.MultipleChoiceField(
                    choices=choices, required=False, widget=forms.CheckboxSelectMultiple
                ),
                forms.CharField(required=False),
            )
        else:
            fields = (
                forms.MultipleChoiceField(
                    choices=choices, required=False, widget=forms.CheckboxSelectMultiple
                ),
            )

        super().__init__(
            fields=fields,
            widget=MultipleChoiceOrOtherWidget(widgets=[f.widget for f in fields]),
            require_all_fields=False,
            *args,
            **kwargs,
        )

    def validate(self, value: list[str]):
        if self.required and not value:
            raise ValidationError(_("Select at least one option"), code="required")

    def compress(self, values: tuple[list[str], str] | tuple[list[str]]) -> list[str]:
        if self.allow_other:
            regular_values = [v for v in values[0] if v != "other"]
            if "other" in values[0]:
                regular_values.append(values[1])

            return regular_values
        else:
            return values[0]


class ParentChildForm(forms.Form):
    parent_form_class: type[forms.ModelForm]
    child_form_class: type[forms.ModelForm]
    relation_name: str
    reverse_name: str

    parent_form: forms.ModelForm
    child_formset: forms.BaseModelFormSet

    def __init__(self, *args, parent_initial=None, child_initial=None, **kwargs):
        self.parent_form = self.get_parent_formset(parent_initial, *args, **kwargs)
        self.child_formset = self.get_child_formset(child_initial, *args, **kwargs)
        # we deliberately do not propagate our arguments to super
        super().__init__()

    def full_clean(self):
        self._errors = ErrorDict(renderer=self.renderer)
        self.cleaned_data = {}

        # Removing short-circuiting from super.

        self._clean_fields()
        self._clean_form()
        self._post_clean()

    def get_parent_formset(self, initial, *args, **kwargs) -> forms.ModelForm:
        return self.parent_form_class(*args, initial=initial, **kwargs)

    def get_child_formset(self, initial, *args, **kwargs) -> forms.BaseModelFormSet:
        # If we have an instance, grab its children for the detail formset
        # Otherwise, use a blank queryset.
        if self.parent_form.instance:
            child_queryset = getattr(self.parent_form.instance, self.reverse_name).all()
        else:
            child_queryset = self.child_form_class.Meta.model.objects.none()

        if "instance" in kwargs:
            # formsets do not want this kwarg
            del kwargs["instance"]

        formset_factory = forms.modelformset_factory(
            self.child_form_class.Meta.model,
            form=self.child_form_class,
            can_delete=True,
            extra=len(initial) if initial else 0,
        )

        formset_factory.deletion_widget = forms.HiddenInput
        return formset_factory(
            *args,
            queryset=child_queryset,
            initial=initial,
            **kwargs,
        )

    def is_valid(self) -> bool:
        # We do this repetitive dance so that our subclasses'
        # clean() methods can add errors on their constituent forms,
        # and have those get picked up, while consuming the cleaned_data
        # _from_ those constituent forms in our clean()
        if not self.parent_form.is_valid() or not self.child_formset.is_valid():
            return False

        if self.errors:
            return False

        if not self.parent_form.is_valid() or not self.child_formset.is_valid():
            return False

        return True

    def add_child_form(self, values: dict[str, str] | None = None):
        if "form-TOTAL_FORMS" in self.child_formset.data:
            try:
                new_data = self.child_formset.data.copy()
                count = int(new_data["form-TOTAL_FORMS"])
                new_data[f"form-{count}-id"] = ""
                if values:
                    for key, value in values.items():
                        new_data[f"form-{count}-{key}"] = value

                count += 1
                new_data["form-TOTAL_FORMS"] = str(count)
                self.child_formset = self.get_child_formset(initial=None, data=new_data)
            except (KeyError, ValueError):
                pass
        else:
            # Form has not been rendered yet.
            self.child_formset.extra += 1

    def delete_child_form(self, index: int):
        new_data = self.child_formset.data.copy()
        if 0 <= index < len(new_data):
            new_data[f"form-{index}-DELETE"] = "on"
            self.child_formset = self.get_child_formset(initial=None, data=new_data)

    def save(self):
        with transaction.atomic():
            parent = self.parent_form.save()

            for child_form in self.child_formset.forms:
                setattr(child_form.instance, self.relation_name, parent)

            self.child_formset.save_existing_objects()
            self.child_formset.save_new_objects()

            return parent


class ApplicationForm(forms.Form):
    """This is a compound form class that represents the content of a
    user-designed models.ApplicationForm"""

    profile_form: forms.ModelForm
    availability_form: forms.Form | None
    role_group_forms: list[forms.Form]
    custom_form: forms.Form | None
    app_form: models.ApplicationForm
    user: models.User | None
    instance: models.Application | None

    def __init__(
        self,
        app_form: models.ApplicationForm,
        user: models.User | None,
        instance: models.Application | None,
        editable: bool,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.app_form = app_form
        self.instance = instance

        # If we have an instance, build a dict of initial values.
        if instance:
            initial = {}
            initial["days"] = instance.availability_by_day
            initial["games"] = instance.availability_by_game.all()
            # This gets filtered below.
            initial["roles"] = instance.roles.all()
            responses_by_question = instance.responses_by_question()
            for question in app_form.form_questions.all():
                if question.id in responses_by_question:
                    content = responses_by_question[question.id].content

                    # Clean up accidentally-stored lists.
                    if isinstance(content, list) and question.kind in [
                        models.QuestionKind.SHORT_TEXT,
                        models.QuestionKind.LONG_TEXT,
                    ]:
                        content = content[0]

                    initial[f"{question.id}"] = content
        else:
            initial = None

        if "prefix" in kwargs:
            kwargs.pop("prefix")
        if "initial" in kwargs:
            kwargs.pop("initial")

        # Generate fields for profile
        profile_form_class = forms.modelform_factory(
            models.User, fields=app_form.requires_profile_fields
        )
        self.profile_form = profile_form_class(
            instance=user, prefix="profile", *args, **kwargs
        )
        for f in self.profile_form.fields.values():
            f.disabled = not editable

        self.user = user

        # Generate fields for availability
        if (
            app_form.application_availability_kind
            == models.ApplicationAvailabilityKind.BY_DAY
        ):
            self.availability_form = forms.Form(
                prefix="days", initial=initial, *args, **kwargs
            )
            self.availability_form.fields["days"] = forms.MultipleChoiceField(
                choices=[(a, a) for a in app_form.event.days()],
                widget=forms.CheckboxSelectMultiple,
                required=True,
                disabled=not editable,
            )
        elif (
            app_form.application_availability_kind
            == models.ApplicationAvailabilityKind.BY_GAME
        ):
            self.availability_form = forms.Form(
                prefix="games", initial=initial, *args, **kwargs
            )
            self.availability_form.fields["games"] = forms.ModelMultipleChoiceField(
                app_form.games(),
                widget=forms.CheckboxSelectMultiple,
                required=True,
                disabled=not editable,
            )
        else:
            self.availability_form = None

        # Generate fields for role groups
        self.role_group_forms = []
        for role_group in app_form.role_groups.all():
            # We need to pass a distinct initial to each role group form
            this_initial = None
            if initial:
                this_initial = copy.copy(initial)
                this_initial["roles"] = this_initial["roles"].filter(
                    role_group_id=role_group.id
                )
            self.role_group_forms.append(
                forms.Form(
                    prefix=f"role-group-{role_group.id}",
                    initial=this_initial,
                    *args,
                    **kwargs,
                )
            )
            # We need to get only the first role with any given name.
            role_ids = set()
            role_names = set()
            for role in role_group.roles.all():
                if role.name not in role_names:
                    role_names.add(role.name)
                    role_ids.add(role.id)
            self.role_group_forms[-1].fields["roles"] = forms.ModelMultipleChoiceField(
                role_group.roles.filter(id__in=role_ids),
                widget=forms.CheckboxSelectMultiple,
                label=role_group.name,
                disabled=not editable,
                required=False,
            )

        # Generate fields for the custom form built by the user
        if app_form.form_questions.all():
            self.custom_form = forms.Form(
                prefix="custom", initial=initial, *args, **kwargs
            )
            for question in app_form.form_questions.all():
                field = None
                match question.kind:
                    case models.QuestionKind.SHORT_TEXT:
                        field = forms.CharField()
                    case models.QuestionKind.LONG_TEXT:
                        field = forms.CharField(widget=forms.Textarea)
                    case models.QuestionKind.SELECT_ONE:
                        field = forms.ChoiceField(
                            choices=[(a, a) for a in question.options],
                            widget=forms.RadioSelect,
                        )
                    case models.QuestionKind.SELECT_MANY:
                        field = MultipleChoiceOrOtherField(
                            choices=[(a, a) for a in question.options],
                            allow_other=question.allow_other,
                        )

                if field:
                    field.label = question.content
                    field.required = question.required
                    field.disabled = not editable
                    self.custom_form.fields[f"{question.id}"] = field
        else:
            self.custom_form = None

    def is_valid(self):
        forms_valid = all(f.is_valid() for f in self.forms)
        if forms_valid:
            roles = models.Role.objects.none()
            for role_group_form in self.role_group_forms:
                if this_group_roles := role_group_form.cleaned_data.get("roles"):
                    roles |= this_group_roles

            have_roles = roles.exists()
            if not have_roles:
                for role_group_form in self.role_group_forms:
                    role_group_form.add_error(
                        None,
                        error={
                            "roles": _("Select at least one role from any role group.")
                        },
                    )

            return have_roles

        return False

    @property
    def forms(self) -> list[forms.Form | forms.ModelForm]:
        return [
            f
            for f in (
                [self.profile_form, self.availability_form]
                + self.role_group_forms
                + [self.custom_form]
            )
            if f
        ]

    def cleaned_data(self) -> list[dict]:
        return [f.cleaned_data for f in self.forms]

    def save(self):
        with transaction.atomic():
            # Create instance if not present.
            if not self.instance:
                self.instance = models.Application(
                    form=self.app_form,
                    user=self.user,
                    status=models.ApplicationStatus.APPLIED,
                )
                self.instance.save()

            # Save profile.
            self.profile_form.save()

            # Save availability
            if (
                self.app_form.application_availability_kind
                == models.ApplicationAvailabilityKind.BY_DAY
            ):
                self.instance.availability_by_day = self.availability_form.cleaned_data[
                    "days"
                ]
            elif (
                self.app_form.application_availability_kind
                == models.ApplicationAvailabilityKind.BY_GAME
            ):
                self.instance.availability_by_game.set(
                    self.availability_form.cleaned_data["games"]
                )

            # Save roles
            roles = models.Role.objects.none()
            for role_group_form in self.role_group_forms:
                if this_group_roles := role_group_form.cleaned_data.get("roles"):
                    roles |= this_group_roles
            self.instance.roles.set(roles)

            # Save custom question answers
            for question in self.app_form.form_questions.all():
                if str(question.id) in self.custom_form.fields:
                    values = self.custom_form.cleaned_data[str(question.id)]
                    response = models.ApplicationResponse.objects.filter(
                        application=self.instance, question=question
                    ).first()
                    if not response:
                        response = models.ApplicationResponse(
                            application=self.instance, question=question
                        )

                    response.content = values
                    response.save()

            self.instance.save()

            return self.instance


class QuestionForm(forms.ModelForm):
    class Meta:
        model = models.Question
        fields = ["content", "kind", "required", "options", "allow_other"]
        widgets = {"kind": forms.HiddenInput(), "content": forms.TextInput}

    options = SeparatedJSONListField(
        widget=forms.Textarea(attrs={"rows": 5}),
        required=False,
        help_text=_("Enter each option on a separate line"),
    )
    allow_other = forms.BooleanField(
        required=False,
        help_text=_('Allow the user to choose "Other" and enter a custom response.'),
    )
    kind: models.QuestionKind

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)

        if self.instance:
            self.kind = self.instance.kind

            if (
                self.instance.application_form
                and not self.instance.application_form.editable
            ):
                self.fields["required"].disabled = True
                self.fields["options"].disabled = True
                self.fields["allow_other"].disabled = True

        if not self.kind:
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

    def clean_options(self):
        options = self.cleaned_data["options"]
        if not options and self.kind in [
            models.QuestionKind.SELECT_ONE,
            models.QuestionKind.SELECT_MANY,
        ]:
            raise forms.ValidationError(
                _(
                    "One or more options is required for Select One and Select Many questions."
                ),
                code="required",
            )

        return options or []


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
            "requires_profile_fields",
        ]
        widgets = {"role_groups": forms.CheckboxSelectMultiple}

    def __init__(self, event: models.Event | None = None, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)
        if event:
            self.fields["role_groups"].queryset = event.role_groups.all()
        elif self.instance:
            self.fields["role_groups"].queryset = self.instance.event.role_groups.all()

        if self.instance and not self.instance.editable:
            # Our instance might not be editable due to receiving applications.
            # Block edits to fields that would cause issues.
            self.fields["role_groups"].disabled = True
            self.fields["application_kind"].disabled = True
            self.fields["application_availability_kind"].disabled = True
            self.fields["requires_profile_fields"].disabled = True


class LeagueForm(forms.ModelForm):
    class Meta:
        model = models.League
        fields = ["name", "slug", "description", "logo", "website", "time_zone"]

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)


class CrewForm(forms.ModelForm):
    class Meta:
        model = models.Crew
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)


class EventForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        required=False,
        queryset=models.EventTemplate.objects.none(),
        widget=forms.HiddenInput,
    )

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
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "role_groups": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, league: models.League | None = None, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)
        if league:
            self.fields["role_groups"].queryset = league.role_groups.all()
            self.fields["template"].queryset = league.event_templates.all()
        elif self.instance:
            self.fields["role_groups"].queryset = self.instance.league.role_groups.all()
            self.fields[
                "template"
            ].queryset = self.instance.league.event_templates.all()


class EventFromTemplateForm(forms.ModelForm):
    class Meta:
        model = models.Event
        fields = [
            "name",
            "start_date",
        ]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, league: models.League, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)


class GameForm(forms.ModelForm):
    class Meta:
        model = models.Game
        fields = [
            "name",
            "home_league",
            "home_team",
            "visiting_league",
            "visiting_team",
            "association",
            "kind",
            "start_time",
            "end_time",
            "role_groups",
        ]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "required": True}
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "required": True}
            ),
            "role_groups": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)


class EventCreateUpdateForm(ParentChildForm):
    parent_form_class = EventForm
    child_form_class = GameForm
    relation_name = "event"
    reverse_name = "games"
    league: models.League
    template: models.EventTemplate | None

    def __init__(
        self,
        league: models.League,
        template: models.EventTemplate | None,
        *args,
        **kwargs,
    ):
        self.league = league
        self.template = template
        super().__init__(*args, league=league, **kwargs)

    def get_parent_formset(self, initial, *args, **kwargs) -> forms.ModelForm:
        if self.template:
            if not initial:
                initial = {}
            initial["template"] = self.template

        return super().get_parent_formset(initial, *args, **kwargs)

    def get_child_formset(self, *args, **kwargs) -> forms.BaseModelFormSet:
        if "league" in kwargs:
            del kwargs["league"]

        formset = super().get_child_formset(*args, **kwargs)

        for form in formset:
            form.fields["role_groups"].queryset = self.league.role_groups.filter(
                event_only=False
            )

        return formset

    def is_valid(self):
        # This is super unintuitive, but is_valid() is where full_clean()
        # gets called on the child forms. That's where timezones get
        # interpreted.
        with timezone.override(self.league.time_zone):
            return super().is_valid()

    def clean(self):
        super().clean()

        # Validate that all Game role groups are a subset of Event role groups
        # m2m fields aren't saved, so use cleaned_data rather than instance.
        event_role_groups = [
            role_group
            for role_group in self.parent_form.cleaned_data.get("role_groups", [])
            if not role_group.event_only
        ]

        for game_form in self.child_formset.forms:
            if not all(
                role_group in event_role_groups
                for role_group in game_form.cleaned_data.get("role_groups", [])
            ):
                game_form.add_error(
                    "role_groups",
                    _("Role groups for Games must be included on the Event"),
                )

        # Assign league.
        self.parent_form.instance.league = self.league

        # Renumber games.
        for index, game_form in enumerate(
            [
                game_form
                for game_form in self.child_formset.forms
                if game_form.cleaned_data.get("DELETE") != "on"
            ]
        ):
            game_form.instance.order_key = index + 1

        # If we're cloning a template, finish by cloning ApplicationFormTemplates
        # FIXME/TODO
        if template := self.parent_form.cleaned_data["template"]:
            pass


class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = models.User.ALLOWED_PROFILE_FIELDS

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)


class SendEmailForm(forms.Form):
    subject = forms.CharField(max_length=256)
    content = forms.CharField(max_length=2048, widget=forms.Textarea)  # TODO

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)
