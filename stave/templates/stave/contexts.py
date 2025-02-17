from stave import models
from dataclasses import dataclass

@dataclass
class ApplicationActionsInputs:
    user: models.User
    application: models.Application
    ApplicationStatus: type
    include_view: bool


@dataclass
class ApplicationTableInputs:
    form: models.ApplicationForm
    applications: list[models.Application]
