Feature: Show Stats page
  Shows the stats page

  Scenario: User opens stats page

    Given a logged-in admin user
    When they open the stats url
    Then they see the stats page
