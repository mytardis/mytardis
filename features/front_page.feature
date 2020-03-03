Feature: Show front page
  Shows the front page

  Scenario: User opens index url

    Given an anonymous user
    When they open the index url
    Then they see the front page

  Scenario: Logged-in user opens index url

    Given a logged-in user
    When they open the index url
    Then they see the user menu
