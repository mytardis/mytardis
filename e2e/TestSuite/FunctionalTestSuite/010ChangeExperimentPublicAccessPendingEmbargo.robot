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
${ExperimentPublicAccess3}      ChangeExperimentACL3

*** Test Cases ***

TEST CASE 10.1:Login as user

    Login       ${AdminUser}     ${AdminPSWD}

TEST CASE 10.2: Create Experiment

    Create Experiment             ${ExperimentPublicAccess3}       Testuser   TestInstitution   Testing description

TEST CASE 10.3: Change Experiment Access Level

    Change Experiment Publlic Access        Ready to be released pending embargo expiry       None

TEST CASE 10.4: Verify Experiment is displayed on My Data page

    Verify page contains item      ${ExperimentPublicAccess3}     xpath://*[@class='nav-link' and @href='/mydata/']

TEST CASE 10.5: Logout and Re-Login as another user

    Logout
    Login        ${User1}       ${User1PSWD}

TEST CASE 10.6: Verify user can not view experiment under Home page

    Open page                        xpath://*[@class='nav-link' and @href='/']
    page should not contain link     ${ExperimentPublicAccess3}

TEST CASE 10.7: Verify user can not view experiment under My Data page

    Open page                        xpath://*[@class='nav-link' and @href='/mydata/']
    page should not contain link     ${ExperimentPublicAccess3}

TEST CASE 10.8: Verify user can not view experiment under Shared page

    Open page                        xpath://*[@class='nav-link' and @href='/shared/']
    page should not contain link     ${ExperimentPublicAccess3}

TEST CASE 10.9: Verify user can not view experiment under Public Data page

    Open page                        xpath://*[@class='nav-link' and @href='/public_data/']
    page should not contain link     ${ExperimentPublicAccess3}


