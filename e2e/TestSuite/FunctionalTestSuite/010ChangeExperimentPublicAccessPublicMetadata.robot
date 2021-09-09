*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot
Resource   ../../Resources/ReusablePaths.robot

Documentation    This file is to test changing experiement public access level

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Variables ***
${ExperimentPublicAccess4}      ChangeExperimentACL4

*** Test Cases ***

TEST CASE 10.1:Login as user

    Login       ${AdminUser}     ${AdminPSWD}

TEST CASE 10.2: Create Experiment

    Create Experiment             ${ExperimentPublicAccess4}       Testuser   TestInstitution   Testing description
    sleep   3
TEST CASE 10.3: Change Experiment Access Level

    Change Experiment Public Access        Public Metadata only (no data file access)        ''
    sleep   3
TEST CASE 10.4: Verify Experiment is displayed on My Data page

    Verify page contains item      ${ExperimentPublicAccess4}     xpath://*[@class='nav-link' and @href='/mydata/']
    sleep   3
TEST CASE 10.5: Logout and Re-Login as another user

    Logout
    Login        ${User1}       ${User1PSWD}

TEST CASE 10.6: Verify user can view and open experiment under Home page

    Verify page contains item           ${ExperimentPublicAccess4}      xpath://*[@class='nav-link' and @href='/']
    sleep   3
TEST CASE 10.7: Verify user can view and open experiment under Public Data page

    Verify page contains item           ${ExperimentPublicAccess4}       xpath://*[@class='nav-link' and @href='/public_data/']
    sleep   3
TEST CASE 10.8: Verify user can not view experiment under My Data page

    Open page                        xpath://*[@class='nav-link' and @href='/mydata/']
    page should not contain link     ${ExperimentPublicAccess4}
    sleep   3
TEST CASE 10.9: Verify user can not view experiment under Shared page

    Open page                        xpath://*[@class='nav-link' and @href='/shared/']
    page should not contain link     ${ExperimentPublicAccess4}
    sleep   3



