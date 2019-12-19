Feature: Show About page
  Shows the about page

  Scenario: User opens about page

    Given an anonymous user
    When they open the about url
    Then they see the about page
