from behave import given, when, then
from bs4 import BeautifulSoup

from tests.factories import UserFactory


@given("a Stave admin user exists")
def given_superuser_exists(context):
    context.superuser = UserFactory.create(is_superuser=True, is_staff=True)
    context.superuser_password = "password123"


@when("the user navigates to the Django Admin login page")
def when_navigate_admin_login(context):
    context.response = context.test.client.get("/admin/login/", follow=True)
    context.test.assertEqual(context.response.status_code, 200)
    context.test.assertTemplateUsed(context.response, "allauth/layouts/base.html")


@when("the user enters valid credentials")
def when_enter_valid_credentials(context):
    # Use Django's test client login method
    login_success = context.test.client.login(
        email=context.superuser.email, password=context.superuser_password
    )
    context.test.assertTrue(login_success)
    # Load the admin dashboard page, mimicking the `next=` behavior
    context.response = context.test.client.get("/admin/")


@then("the Django Admin dashboard is displayed")
def then_admin_dashboard_displayed(context):
    context.test.assertEqual(context.response.status_code, 200)

    soup = BeautifulSoup(context.response.content, "html.parser")
    title_text = soup.find("title").text
    context.test.assertEqual(title_text, "Site administration | Django site admin")
