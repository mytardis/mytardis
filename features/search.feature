Feature: Show Search page
  Shows the search page

  Scenario: User opens search page

    Given a logged-in user
    When they open the search url
    Then they see the search page
