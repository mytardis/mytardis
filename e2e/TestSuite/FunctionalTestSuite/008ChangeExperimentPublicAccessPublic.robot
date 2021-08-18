*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot
Resource   ../../Resources/ReusablePaths.robot

Documentation    This file is to test changing experiement public access level

Suite Setup         Open Home page
#Suite Teardown      close all browsers

*** Variables ***
${ExperimentPublicAccess1}      ChangeExperimentACL1

*** Test Cases ***

TEST CASE 8.1:Login as user

    Login       ${AdminUser}     ${AdminPSWD}

TEST CASE 8.2: Create Experiment

    Create Experiment             ${ExperimentPublicAccess1}       Testuser   TestInstitution   Testing description

TEST CASE 8.3: Change Experiment Access Level

    Change Experiment Publlic Access        Public         1

TEST CASE 8.4: Logout and Re-Login as another user

    Logout
    Login        ${User1}       ${User1PSWD}

TEST CASE 8.5: Verify user can view and open experiment under Home page

    Verify page contains item           ${ExperimentPublicAccess1}       xpath://*[@class='nav-link' and @href='/']

TEST CASE 8.6: Verify user can view and open experiment under Public Data page

    Verify page contains item           ${ExperimentPublicAccess1}       xpath://*[@class='nav-link' and @href='/public_data/']
