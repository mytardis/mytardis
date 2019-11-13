Feature: Show the auth methods page

  Scenario: User accesses auth methods ("Link Accounts") page

    Given a logged-in user with change user-auth perms
    When they open the auth methods url
    Then they see the auth methods page
