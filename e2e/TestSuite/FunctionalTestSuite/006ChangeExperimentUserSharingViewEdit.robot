*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot
Resource   ../../Resources/ReusablePaths.robot

Documentation    This file is to test experiement user sharing

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Variables ***
${SharedExperiment2}        006ChngExpUserSharingViewEdit

*** Test Cases ***

TEST CASE 6.1:Login as user

    Login                   ${AdminUser}     ${AdminPSWD}

TEST CASE 6.2: Create Experiment

    Create Experiment        ${SharedExperiment2}       Testuser   TestInstitution   Testing description
    sleep   3
TEST CASE 6.3: Add user to Experiment Sharing as View Only

    Add new user to Sharing             ${User1}      View and Edit
    sleep   3
TEST CASE 6.4: Verify user permissions are displayed under User Sharing

    Verify user permissions are displayed       ${User1}      Read
    Verify user permissions are displayed       ${User1}      Edit

    Logout

TEST CASE 6.5:Login as user

    Login       ${User1}      ${User1PSWD}

TEST CASE 6.6: Verify user can view and open experiment under Home page

    Verify page contains item           ${SharedExperiment2}       xpath://*[@class='nav-link' and @href='/']
    sleep   3
TEST CASE 6.7: Edit Experiment

    Edit Experiment         ${SharedExperiment2}   EditTestuser  EditTestInstitution  EditTestingDescription
    sleep   3
TEST CASE 6.8: Add Experiment Metadata

    Add Experiment Metadata     TestSchema   Adding value to Param 1    Adding value to Param 2
    sleep   3
TEST CASE 6.9: Edit Experiment Metadata

    Edit Experiment Metadata    EditParam1      EditParam2
    sleep   3
TEST CASE 6.10: Add Dataset

    Add DataSet                 ${DatasetName}        DataDirectory       DataInstrument
    sleep   3
TEST CASE 6.11: Verify Dataset is Not displayed on My Data page

    Verify page does Not contain item   ${DatasetName}     xpath://*[@class='nav-link' and @href='/mydata/']
    sleep   3

TEST CASE 6.12: Verify Dataset is displayed on Home page

    Verify page contains item    ${DatasetName}     xpath://*[@class='nav-link' and @href='/']
    sleep   3
TEST CASE 6.13: Edit Dataset

    Edit DataSet            ${EditDataSetName}        EditDataDirectory       EditDataInstrument
    sleep   3
TEST CASE 6.14: Add Dataset Metadata

    Add Dataset MetaData    DatasetSchema   Adding value to Param 1    Adding value to Param 2
    sleep   3
TEST CASE 6.15: Edit Dataset Metadata

    Edit Dataset MetaData   Edit Adding value to Param 1        Edit Adding value to Param 2
    sleep   3
TEST CASE 6.16: Verify user can see experiment under Shared page

    Verify page contains item       ${SharedExperiment2}       xpath://*[@class='nav-link' and @href='/shared/']
    sleep   3
TEST CASE 6.17: Verify user can Not see experiment under Mydata page

    Open page                             xpath://*[@class='nav-link' and @href='/mydata/']
    Verify page does Not contain item     element      ${SharedExperiment2}
    sleep   3







