from datetime import datetime, timedelta
from behave import given, when, then
from bs4 import BeautifulSoup
from stave.models import (
    Event,
    ApplicationForm,
    Application,
    ApplicationStatus,
    RoleGroup,
    ApplicationKind,
    ApplicationAvailabilityKind,
    LeagueUserPermission,
    UserPermission,
    EventStatus,
)

from tests.factories import LeagueFactory, UserFactory


@given("a regular user exists")
def given_regular_user_exists(context):
    context.user = UserFactory.create()
    context.user_password = "password123"


@given("there are open application forms available")
def given_open_application_forms(context):
    # Create a league and event with open application forms
    league = LeagueFactory.create(enabled=True)

    future_date = datetime.now() + timedelta(days=30)

    event = Event.objects.create(
        name="Test Event",
        slug="test-event",
        league=league,
        start_date=future_date.date(),
        end_date=future_date.date(),
        status=EventStatus.OPEN,
    )

    role_group = RoleGroup.objects.create(name="Test Role", league=league)

    context.application_form = ApplicationForm.objects.create(
        event=event,
        slug="test-form",
        close_date=future_date.date(),
        application_kind=ApplicationKind.ASSIGN_ONLY,
        application_availability_kind=ApplicationAvailabilityKind.WHOLE_EVENT,
        intro_text="Test application form for testing purposes.",
    )
    context.application_form.role_groups.add(role_group)


@given("the user has submitted applications")
def given_user_has_applications(context):
    # TODO: Replace with a Factory pattern
    # Ensure we have an application form first
    if not hasattr(context, "application_form"):
        context.execute_steps("Given there are open application forms available")

    context.application = Application.objects.create(
        user=context.user,
        form=context.application_form,
        status=ApplicationStatus.APPLIED,
    )


@given("the user manages events")
def given_user_manages_events(context):
    # Give the user permissions to manage the league
    # TODO: Replace with a Factory pattern
    if not hasattr(context, "application_form"):
        context.execute_steps("Given there are open application forms available")

    # Add the user as an event manager
    LeagueUserPermission.objects.create(
        user=context.user,
        league=context.application_form.event.league,
        permission=UserPermission.EVENT_MANAGER,
    )

    # Create some applications to test pending/open indicators with distinct users
    context.open_application = Application.objects.create(
        user=UserFactory.create(),
        form=context.application_form,
        status=ApplicationStatus.APPLIED,  # This is an "open" application
    )
    context.pending_application = Application.objects.create(
        user=UserFactory.create(),
        form=context.application_form,
        status=ApplicationStatus.INVITATION_PENDING,  # This is a "pending" application
    )


@when("the user navigates to the home page")
def when_navigate_home(context):
    context.response = context.test.client.get("/", follow=True)
    context.test.assertEqual(context.response.status_code, 200)


@when("an unauthenticated user navigates to the home page")
def when_unauthenticated_navigate_home(context):
    # Ensure we're not logged in
    context.test.client.logout()
    context.response = context.test.client.get("/", follow=True)
    context.test.assertEqual(context.response.status_code, 200)


@when("the user logs in with valid credentials")
def when_login_with_valid_credentials(context):
    # Use Django's test client login method
    login_success = context.test.client.login(
        email=context.user.email, password=context.user_password
    )
    context.test.assertTrue(login_success)
    # Reload the home page after login
    context.response = context.test.client.get("/")


@then("the user home page is displayed")
def then_home_page_displayed(context):
    context.test.assertEqual(context.response.status_code, 200)
    context.test.assertTemplateUsed(context.response, "stave/home.html")

    soup = BeautifulSoup(context.response.content, "html.parser")
    # Check for welcome message
    welcome_text = soup.find(text=lambda t: t and "Welcome to Stave" in t)
    context.test.assertIsNotNone(welcome_text)


@then('the user sees the "{section_name}" section')
def then_user_sees_section(context, section_name):
    soup = BeautifulSoup(context.response.content, "html.parser")
    section_header = soup.find("h2", string=section_name)
    context.test.assertIsNotNone(
        section_header, f"Could not find '{section_name}' section header"
    )


@then("the user sees their calendar widget")
def then_user_sees_calendar(context):
    soup = BeautifulSoup(context.response.content, "html.parser")
    # Look for calendar include or calendar-related elements
    calendar_elements = soup.find_all(string=lambda t: t and "calendar" in t.lower())
    context.test.assertTrue(len(calendar_elements) > 0, "Calendar widget not found")


@then('the user sees "{message}" in the My Applications section')
def then_user_sees_message_in_applications(context, message):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Find the My Applications section
    my_apps_header = soup.find("h2", string="My Applications")
    context.test.assertIsNotNone(my_apps_header)

    # Look for the message in the same article
    article = my_apps_header.find_parent("article")
    message_text = article.find(text=lambda t: t and message in t)
    context.test.assertIsNotNone(
        message_text, f"Could not find message '{message}' in My Applications section"
    )


@then('the user sees "{message}" in the My Events section')
def then_user_sees_message_in_events(context, message):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Find the My Events section
    my_events_header = soup.find("h2", string="My Events")
    context.test.assertIsNotNone(my_events_header)

    # Look for the message in the same article
    article = my_events_header.find_parent("article")
    message_text = article.find(text=lambda t: t and message in t)
    context.test.assertIsNotNone(
        message_text, f"Could not find message '{message}' in My Events section"
    )


@then("the user can see application forms grouped by event")
def then_application_forms_grouped_by_event(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Find the Open Applications section
    open_apps_header = soup.find("h2", string="Open Applications")
    context.test.assertIsNotNone(open_apps_header)

    # Look for event links in the same article
    article = open_apps_header.find_parent("article")
    event_links = article.find_all("a", href=True)
    context.test.assertTrue(
        len(event_links) > 0, "No event links found in Open Applications"
    )


@then("each application form shows the roles available")
def then_application_shows_roles(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Look for "Apply as" text which indicates roles
    apply_links = soup.find_all(text=lambda t: t and "Apply as" in t)
    context.test.assertTrue(
        len(apply_links) > 0, "No role information found in applications"
    )


@then("each application form shows the closing date if applicable")
def then_application_shows_closing_date(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Look for closing date information
    closes_text = soup.find_all(text=lambda t: t and "closes" in t)
    context.test.assertTrue(
        len(closes_text) > 0,
        "Expected to find closing date information for application forms",
    )


@then("the user can click on application links to apply")
def then_user_can_click_application_links(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Find links that contain "/apply/" in the href or "Apply" in the text
    apply_links = soup.find_all("a", href=True)
    application_links = [
        link
        for link in apply_links
        if "/apply/" in link.get("href", "") or "Apply" in link.get_text()
    ]
    context.test.assertTrue(len(application_links) > 0, "No application links found")


@then('the user sees their applications in the "My Applications" section')
def then_user_sees_their_applications(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Find the My Applications section
    my_apps_header = soup.find("h2", string="My Applications")
    context.test.assertIsNotNone(my_apps_header)

    # Look for application links in the same article
    article = my_apps_header.find_parent("article")
    app_links = article.find_all("a", href=True)
    context.test.assertTrue(
        len(app_links) > 0, "No application links found in My Applications"
    )


@then("each application shows the event name")
def then_application_shows_event_name(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # The event name should be in the application link text
    my_apps_header = soup.find("h2", string="My Applications")
    article = my_apps_header.find_parent("article")

    # Look for the test event name
    event_text = article.find(text=lambda t: t and "Test Event" in t)
    context.test.assertIsNotNone(event_text, "Event name not found in application")


@then("each application shows the current status")
def then_application_shows_status(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Status should be shown in parentheses
    status_text = soup.find(text=lambda t: t and "Applied" in t)
    context.test.assertIsNotNone(status_text, "Application status not found")


@then("the user can click on applications to view details")
def then_user_can_click_applications(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Find My Applications section and look for application/<uuid>/ URLs
    my_apps_header = soup.find("h2", string="My Applications")
    article = my_apps_header.find_parent("article")

    app_links = article.find_all("a", href=True)
    view_links = [link for link in app_links if "/application/" in link.get("href", "")]
    context.test.assertTrue(len(view_links) > 0, "No view application links found")


@then('the user sees their events in the "My Events" section')
def then_user_sees_their_events(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Find the My Events section
    my_events_header = soup.find("h2", string="My Events")
    context.test.assertIsNotNone(my_events_header)

    # Look for event links in the same article
    article = my_events_header.find_parent("article")
    event_links = article.find_all("a", href=True)
    context.test.assertTrue(len(event_links) > 0, "No event links found in My Events")


@then("each event shows application forms with role groups")
def then_event_shows_application_forms(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Look for role group names in the My Events section
    my_events_header = soup.find("h2", string="My Events")
    article = my_events_header.find_parent("article")

    # Look for role group information
    role_text = article.find(text=lambda t: t and "Test Role" in t)
    context.test.assertIsNotNone(role_text, "Role group information not found")


@then("pending applications are highlighted with counts")
def then_pending_applications_highlighted(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Look for pending application indicators
    pending_elements = soup.find_all("span", class_="cta")
    pending_found = any(
        "pending" in elem.get_text().lower() for elem in pending_elements
    )
    context.test.assertTrue(
        pending_found,
        "Expected to find pending application indicators for event managers",
    )


@then("open applications are highlighted with counts")
def then_open_applications_highlighted(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Look for open application indicators
    open_elements = soup.find_all("span", class_="cta")
    open_found = any("open" in elem.get_text().lower() for elem in open_elements)
    context.test.assertTrue(
        open_found,
        "Expected to find open application indicators for event managers",
    )


@then("multiple embedded video tutorials are displayed")
def then_video_tutorials_displayed(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    # Look for iframe elements (YouTube embeds)
    iframes = soup.find_all("iframe")
    youtube_iframes = [
        iframe for iframe in iframes if "youtube" in iframe.get("src", "")
    ]
    context.test.assertTrue(
        len(youtube_iframes) >= 4,
        f"Expected at least 4 YouTube videos, found {len(youtube_iframes)}",
    )


@then('the user sees the "Join Now" section instead of personalized content')
def then_user_sees_join_now_section(context):
    soup = BeautifulSoup(context.response.content, "html.parser")
    join_now_header = soup.find("h2", string="Join Now")
    context.test.assertIsNotNone(
        join_now_header, "Join Now section not found for unauthenticated user"
    )


@then('the user does not see "My Applications" or "My Events" sections')
def then_user_does_not_see_personal_sections(context):
    soup = BeautifulSoup(context.response.content, "html.parser")

    my_apps_header = soup.find("h2", string="My Applications")
    context.test.assertIsNone(
        my_apps_header,
        "My Applications section should not be visible to unauthenticated users",
    )

    my_events_header = soup.find("h2", string="My Events")
    context.test.assertIsNone(
        my_events_header,
        "My Events section should not be visible to unauthenticated users",
    )
