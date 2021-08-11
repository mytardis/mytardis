*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test experiement creation, adding metadata to experiment, adding datasets to experiment, adding metadata to experiment

Suite Setup         Open Home page
#Suite Teardown      close all browsers

*** Variables ***
${SharedExperimentName}     SharedExp
${Sharing}                  xpath://*[@title='Sharing']
${ChngUserSharing}          xpath://*[@class='share_link btn btn-outline-secondary btn-sm' and @title='Change']
${User}                     id:id_entered_user
${PermissionsList}          id:id_permission
${AddUser}                  id:user


*** Test Cases ***

TEST CASE 5.1:Login as user

    Login       joe     12345

TEST CASE 5.2: Create Experiment

    Create Experiment        ${SharedExperimentName}       Testuser   TestInstitution   Testing description

TEST CASE 5.3: Add user to Experiment Sharing as View Only

    Add new user to Sharing             ann      View Only

TEST CASE 5.4: Verify user permissions are displayed under User Sharing

    Verify user permissions are displayed       ann     Read

    Logout

TEST CASE 5.5:Login as user

    Login       ann     12345

TEST CASE 5.6: Verify user can and open experiment under Home page

    Verify page contains item       ${SharedExperimentName}       xpath://*[@class='nav-link' and @href='/']

TEST CASE 5.7: Verify user can see experiment under Shared page

    Verify page contains item       ${SharedExperimentName}       xpath://*[@class='nav-link' and @href='/shared/']

TEST CASE 5.8: Verify user can Not see experiment under Mydata page

    Verify page does Not contain item     xpath://*[@class='nav-link' and @href='/mydata/']       element      ${SharedExperimentName}


*** Keywords ***

Add new user to Sharing
    [Arguments]                         ${Username}         ${Permissions}
    wait until element is enabled       ${Sharing}
    click element                       ${Sharing}

    wait until element is enabled       ${ChngUserSharing}
    click element                       ${ChngUserSharing}

    wait until element is enabled       ${User}
    input text                          ${User}                       ${Username}

    wait until element is enabled       ${PermissionsList}
    select from list by label           ${PermissionsList}            ${Permissions}

    wait until element is enabled       ${AddUser}
    click element                       ${AddUser}

    press keys    None      ESC

Verify user permissions are displayed
    [Arguments]                         ${Username}             ${Permissions}
    wait until element is enabled       xpath://table//tr/td[contains(text(), '${Username}')]/ancestor::tr/td[3]//*[contains(text(),'${Permissions}')]
    element should contain              xpath://table//tr/td[contains(text(), '${Username}')]/ancestor::tr/td[3]//*[contains(text(),'${Permissions}')]      ${Permissions}



