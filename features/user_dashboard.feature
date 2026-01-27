Feature: User Dashboard and Home Page

    As a logged-in user
    I want to see my personalized dashboard
    So that I can quickly access my applications, events, and available opportunities

Background:
    Given a regular user exists

Scenario: Authenticated user sees personalized dashboard sections
    When the user navigates to the home page
    And the user logs in with valid credentials
    Then the user home page is displayed
    And the user sees the "Open Applications" section
    And the user sees the "My Applications" section
    And the user sees the "Staffing" section
    And the user sees their calendar widget

Scenario: User with no applications sees empty state messages
    When the user navigates to the home page
    And the user logs in with valid credentials
    Then the user sees "You don't have any applications pending right now." in the My Applications section
    And the user sees "You aren't managing any events." in the Staffing section

Scenario: User can access application links from Open Applications section
    Given there are open application forms available
    When the user navigates to the home page
    And the user logs in with valid credentials
    Then the user can see application forms grouped by event
    And each application form shows the roles available
    And each application form shows the closing date if applicable
    And the user can click on application links to apply

Scenario: User can view their submitted applications
    Given the user has submitted applications
    When the user navigates to the home page
    And the user logs in with valid credentials
    Then the user sees their applications in the "My Applications" section
    And each application shows the event name
    And each application shows the current status
    And the user can click on applications to view details

Scenario: Event manager sees their managed events
    Given the user manages events
    When the user navigates to the home page
    And the user logs in with valid credentials
    Then the user sees their events in the "Staffing" section
    And each event shows application forms with role groups
    And pending applications are highlighted with counts
    And open applications are highlighted with counts

Scenario: Unauthenticated user sees limited content
    When an unauthenticated user navigates to the home page
    Then the user sees the "Open Applications" section
    And the user sees the "Join Now" section instead of personalized content
    And the user does not see "My Applications" or "Staffing" sections
