Feature: Show the SFTP instructions and keys pages

  Scenario: User accesses the SFTP instructions page

    Given a logged-in user
    When they open the SFTP index url
    Then they see the SFTP instructions page

  Scenario: User accesses the SFTP keys page

    Given a logged-in user
    When they open the SFTP keys url
    Then they see the SFTP keys page
