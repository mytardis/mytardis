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
    When they click the Metadata link
    Then the experiment metadata tab content is shown
    When they click the Sharing link
    Then the experiment sharing tab content is shown
    # When they click the Change Public Access link
    # Then they see the Change Public Access form
    When they click the Add New dataset button
    Then they see the dataset creation form
    When they fill in the Add Dataset form and click Save
    Then a new dataset is created
    When they open the My Data url
    Then they see the newly created experiment
    When they open the experiment url
    Then they see the newly created dataset
