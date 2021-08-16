*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot
Resource   ../../Resources/ReusablePaths.robot

Documentation    This file is to test experiement user sharing

Suite Setup         Open Home page
#Suite Teardown      close all browsers

*** Variables ***
${GroupShareExperiment}     GroupShareExperiment2

*** Test Cases ***

TEST CASE 13.1:Login as user

    Login                   ${AdminUser}     ${AdminPSWD}

TEST CASE 13.2: Create Experiment

    Create Experiment        ${GroupShareExperiment}       Testuser   TestInstitution   Testing description

TEST CASE 13.3: Add user to Experiment Sharing as View Only

    Add new group to Sharing             ${GroupName1}       View and Edit

TEST CASE 13.4: Verify user permissions are displayed under User Sharing

    Verify user permissions are displayed       ${GroupName1}       Read
    Verify user permissions are displayed       ${GroupName1}       Edit

    Logout

TEST CASE 13.5:Login as user

    Login       ${User1}      ${User1PSWD}

TEST CASE 13.6: Verify user can view and open experiment under Home page

    Verify page contains item           ${GroupShareExperiment}       xpath://*[@class='nav-link' and @href='/']

TEST CASE 13.7: Edit Experiment

    Edit Experiment         ${GroupShareExperiment}   EditTestuser  EditTestInstitution  EditTestingDescription

TEST CASE 13.8: Add Experiment Metadata

    Add Experiment Metadata     TestSchema   Adding value to Param 1    Adding value to Param 2

TEST CASE 13.9: Edit Experiment Metadata

    Edit Experiment Metadata    EditParam1      EditParam2

TEST CASE 13.10: Add Dataset

    Add DataSet                 ${DatasetName}        DataDirectory       DataInstrument

TEST CASE 13.11: Verify Dataset is displayed on My Data page

    Verify page contains item   ${DatasetName}     xpath://*[@class='nav-link' and @href='/mydata/']

TEST CASE 13.12: Verify Dataset is displayed on Home page

    Verify page contains item    ${DatasetName}     xpath://*[@class='nav-link' and @href='/']

TEST CASE 13.13: Edit Dataset

    Edit DataSet            ${EditDataSetName}        EditDataDirectory       EditDataInstrument

TEST CASE 13.14: Add Dataset Metadata

    Add Dataset MetaData    DatasetSchema   Adding value to Param 1    Adding value to Param 2

TEST CASE 13.15: Edit Dataset Metadata

    Edit Dataset MetaData   Edit Adding value to Param 1        Edit Adding value to Param 2

TEST CASE 13.16: Verify user can see experiment under Shared page

    Verify page contains item       ${GroupShareExperiment}       xpath://*[@class='nav-link' and @href='/shared/']

TEST CASE 13.17: Verify user can Not see experiment under Mydata page

    Open page                             xpath://*[@class='nav-link' and @href='/mydata/']
    Verify page does Not contain item     element      ${GroupShareExperiment}








