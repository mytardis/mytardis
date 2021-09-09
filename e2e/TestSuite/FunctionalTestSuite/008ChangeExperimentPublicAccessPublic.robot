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
${ExperimentPublicAccess1}      ChangeExperimentACL1

*** Test Cases ***

TEST CASE 8.1:Login as user

    Login       ${AdminUser}     ${AdminPSWD}

TEST CASE 8.2: Create Experiment

    Create Experiment             ${ExperimentPublicAccess1}       Testuser   TestInstitution   Testing description
    sleep   3
TEST CASE 8.3: Verify Experiment is displayed on My Data page

    Verify page contains item      ${ExperimentPublicAccess1}     xpath://*[@class='nav-link' and @href='/mydata/']
    sleep   3
TEST CASE 8.4: Logout and Re-Login as another user

    Logout
    Login        ${User1}       ${User1PSWD}

TEST CASE 8.5: Verify user can not view experiment under Home page

    Open page                        xpath://*[@class='nav-link' and @href='/']
    page should not contain link     ${ExperimentPublicAccess1}
    sleep   3
TEST CASE 8.6: Verify user can not view experiment under My Data page

    Open page                        xpath://*[@class='nav-link' and @href='/mydata/']
    page should not contain link     ${ExperimentPublicAccess1}
    sleep   3
TEST CASE 8.7: Verify user can not view experiment under Shared page

    Open page                        xpath://*[@class='nav-link' and @href='/shared/']
    page should not contain link     ${ExperimentPublicAccess1}
    sleep   3
TEST CASE 8.8: Verify user can not view experiment under Public Data page

    Open page                        xpath://*[@class='nav-link' and @href='/public_data/']
    page should not contain link     ${ExperimentPublicAccess1}
    sleep   3
TEST CASE 8.9:Login as user

    Logout
    Login       ${AdminUser}     ${AdminPSWD}

TEST CASE 8.10: Change Experiment Access Level

    Verify page contains item               ${ExperimentPublicAccess1}       xpath://*[@class='nav-link' and @href='/']
    Change Experiment Public Access        Public         1
    sleep   3
TEST CASE 8.11: Logout and Re-Login as another user

    Logout
    Login        ${User1}       ${User1PSWD}

TEST CASE 8.12: Verify user can view and open experiment under Home page

    Verify page contains item           ${ExperimentPublicAccess1}       xpath://*[@class='nav-link' and @href='/']
    sleep   3
TEST CASE 8.13: Verify user can view and open experiment under Public Data page

    Verify page contains item           ${ExperimentPublicAccess1}       xpath://*[@class='nav-link' and @href='/public_data/']
    sleep   3
