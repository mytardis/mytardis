Feature: Show front page
  Shows the front page

  Scenario: User opens mytardis url

    Given an anonymous user
    When they open the url
    Then they see the front page
