"""View tests to detect N+1 queries via django-zeal."""

import pytest
from django.test import Client

from tests.factories import (
    ApplicationFactory,
    RoleFactory,
    RoleGroupFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def auth_client(user_factory):
    client = Client()
    user = user_factory(preferred_name="Test User")
    client.force_login(user)
    client.user = user
    return client


@pytest.mark.usefixtures("tournament")
class TestHomeView:
    def test_anonymous(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_authenticated(self, auth_client):
        response = auth_client.get("/")
        assert response.status_code == 200

    def test_authenticated_with_applications(self, auth_client, tournament):
        form = tournament.application_forms.first()
        ApplicationFactory(user=auth_client.user, form=form)
        response = auth_client.get("/")
        assert response.status_code == 200

    def test_event_manager(self, client, event_manager_user):
        client.force_login(event_manager_user)
        response = client.get("/")
        assert response.status_code == 200


class TestEventDetailView:
    def test_event_detail(self, client, tournament):
        league = tournament.league
        response = client.get(f"/_/{league.slug}/events/{tournament.slug}/")
        assert response.status_code == 200


@pytest.mark.usefixtures("tournament")
class TestMyEventsView:
    def test_my_events(self, client, event_manager_user):
        client.force_login(event_manager_user)
        response = client.get("/my-events/")
        assert response.status_code == 200


class TestMyApplicationsView:
    def test_my_applications(self, auth_client, tournament):
        form = tournament.application_forms.first()
        ApplicationFactory(user=auth_client.user, form=form)
        response = auth_client.get("/my-applications/")
        assert response.status_code == 200


class TestRoleGroupListView:
    def test_role_group_list(self, client, enabled_league, league_manager_user):
        client.force_login(league_manager_user)
        for i in range(3):
            rg = RoleGroupFactory(league=enabled_league, name=f"RG {i}")
            RoleFactory(role_group=rg, name=f"Role {i}a")
            RoleFactory(role_group=rg, name=f"Role {i}b")
        response = client.get(f"/_/{enabled_league.slug}/role-groups/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "RG 0" in content
        assert "RG 2" in content


class TestLeaguePermissionListView:
    def test_permission_list(self, client, enabled_league, league_manager_user):
        client.force_login(league_manager_user)
        response = client.get(f"/_/{enabled_league.slug}/user-permissions/")
        assert response.status_code == 200


@pytest.mark.usefixtures("tournament")
class TestOpenApplicationsView:
    def test_open_applications(self, auth_client):
        response = auth_client.get("/open-applications/")
        assert response.status_code == 200


class TestLeagueDetailView:
    def test_anonymous(self, client, tournament):
        league = tournament.league
        response = client.get(f"/_/{league.slug}/")
        assert response.status_code == 200


@pytest.mark.usefixtures("tournament")
class TestEventListView:
    def test_anonymous(self, client):
        response = client.get("/events/")
        assert response.status_code == 200

    def test_authenticated(self, auth_client):
        response = auth_client.get("/events/")
        assert response.status_code == 200


@pytest.mark.usefixtures("enabled_league")
class TestLeagueListView:
    def test_anonymous(self, client):
        response = client.get("/leagues/")
        assert response.status_code == 200


class TestApplicationFormView:
    def test_application_form(self, auth_client, tournament):
        league = tournament.league
        form = tournament.application_forms.first()
        response = auth_client.get(
            f"/_/{league.slug}/events/{tournament.slug}/forms/{form.slug}/"
        )
        assert response.status_code == 200
