Feature: Create a Dataset
  Creates an experiment and a dataset

  Scenario: Logged-in user creates an experiment

    Given a logged-in user
    When they open the My Data url
    Then they see the Create Experiment button
    When they click the Create Experiment button
    Then they see the experiment creation form
    When they fill in the experiment creation form and click Save
    Then a new experiment is created
    When they click the Add New button
    Then they see the dataset creation form
    When they fill in the Add Dataset form and click Save
    Then a new dataset is created
