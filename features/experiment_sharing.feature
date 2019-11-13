Feature: Access Shared and Public Experiments

  Scenario: User accesses shared experiment

    Given a logged-in experiment-sharing user
    When they open the shared experiments url
    Then they see the shared experiment

  Scenario: User accesses public experiment

    Given a public experiment
    When they open the public experiments url
    Then they see the public experiment
