Feature: Access Dataset with files

  Scenario: User accesses dataset with files

    Given a logged-in user with dataset access
    When they open the dataset view url
    Then they see the dataset with files
