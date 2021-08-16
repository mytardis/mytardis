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
${ExperimentPublicAccess4}      ChangeExperimentACL4

*** Test Cases ***

TEST CASE 11.1:Login as user

    Login       ${AdminUser}     ${AdminPSWD}

TEST CASE 11.2: Create Experiment

    Create Experiment             ${ExperimentPublicAccess4}       Testuser   TestInstitution   Testing description

TEST CASE 11.3: Change Experiment Access Level

    Change Experiment Publlic Access        No public access (hidden)       ''

TEST CASE 11.4: Verify Experiment is displayed on My Data page

    Verify page contains item      ${ExperimentPublicAccess4}     xpath://*[@class='nav-link' and @href='/mydata/']

TEST CASE 11.5: Logout and Re-Login as another user

    Logout
    Login        ${User1}       ${User1PSWD}

TEST CASE 11.6: Verify user can view and open experiment under Home page

    Verify page contains item           ${ExperimentPublicAccess4}      xpath://*[@class='nav-link' and @href='/']

TEST CASE 11.7: Verify user can view and open experiment under Public Data page

    Verify page contains item           ${ExperimentPublicAccess4}       xpath://*[@class='nav-link' and @href='/public_data/']

TEST CASE 11.8: Verify user can not view experiment under My Data page

    Open page                        xpath://*[@class='nav-link' and @href='/mydata/']
    page should not contain link     ${ExperimentPublicAccess4}

TEST CASE 11.8: Verify user can not view experiment under Shared page

    Open page                        xpath://*[@class='nav-link' and @href='/shared/']
    page should not contain link     ${ExperimentPublicAccess4}




