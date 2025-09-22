Feature: Django Admin Authentication

Scenario: Stave admin user can log in to Django Admin
    Given a Stave admin user exists
    When the user navigates to the Django Admin login page
    And the user enters valid credentials
    Then the Django Admin dashboard is displayed
