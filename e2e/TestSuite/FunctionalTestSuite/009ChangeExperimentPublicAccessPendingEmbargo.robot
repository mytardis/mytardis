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
${ExperimentPublicAccess3}      ChangeExperimentACL3

*** Test Cases ***

TEST CASE 9.1:Login as user

    Login       ${AdminUser}     ${AdminPSWD}

TEST CASE 9.2: Create Experiment

    Create Experiment             ${ExperimentPublicAccess3}       Testuser   TestInstitution   Testing description
    sleep   3
TEST CASE 9.3: Change Experiment Access Level

    Change Experiment Public Access        Ready to be released pending embargo expiry       None
    sleep   3
TEST CASE 9.4: Verify Experiment is displayed on My Data page

    Verify page contains item      ${ExperimentPublicAccess3}     xpath://*[@class='nav-link' and @href='/mydata/']
    sleep   3
TEST CASE 9.5: Logout and Re-Login as another user

    Logout
    Login        ${User1}       ${User1PSWD}

TEST CASE 9.6: Verify user can not view experiment under Home page

    Open page                        xpath://*[@class='nav-link' and @href='/']
    page should not contain link     ${ExperimentPublicAccess3}
    sleep   3
TEST CASE 9.7: Verify user can not view experiment under My Data page

    Open page                        xpath://*[@class='nav-link' and @href='/mydata/']
    page should not contain link     ${ExperimentPublicAccess3}
    sleep   3
TEST CASE 9.8: Verify user can not view experiment under Shared page

    Open page                        xpath://*[@class='nav-link' and @href='/shared/']
    page should not contain link     ${ExperimentPublicAccess3}
    sleep   3
TEST CASE 9.9: Verify user can not view experiment under Public Data page

    Open page                        xpath://*[@class='nav-link' and @href='/public_data/']
    page should not contain link     ${ExperimentPublicAccess3}
    sleep   3

