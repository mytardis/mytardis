Feature: Show Facility Overview

  Scenario: User opens facility overview

    Given a logged-in facility manager
    When they open the facility overview url
    Then they see the facility overview page
