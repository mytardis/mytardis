Feature: Show manage groups page
  Shows the manage groups page

  Scenario: User opens manage groups page

    Given a logged-in admin user
    When they open the manage groups url
    Then they see the manage groups page
