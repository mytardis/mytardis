Feature: Show the Migrate My Account page

  Scenario: User accesses Migrate My Account page

    Given a logged-in user with account migration perms
    When they open the account migration url
    Then they see the Migrate My Account page
