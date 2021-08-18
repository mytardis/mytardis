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
${SharedExperiment3}        SharedExp3

*** Test Cases ***

TEST CASE 7.1:Login as user

    Login                   ${AdminUser}     ${AdminPSWD}

TEST CASE 7.2: Create Experiment

    Create Experiment        ${SharedExperiment3}       Testuser   TestInstitution   Testing description

TEST CASE 7.3: Add user to Experiment Sharing as View Only

    Add new user to Sharing             ${User3}       Full Owner

TEST CASE 7.4: Verify user permissions are displayed under User Sharing

    Verify user permissions are displayed       ${User3}      Read
    Verify user permissions are displayed       ${User3}      Edit
    Verify user permissions are displayed       ${User3}      Owner

    Logout

TEST CASE 7.5:Login as user

    Login       ${User3}      ${User3PSWD}

TEST CASE 7.6: Verify user can view and open experiment under Home page

    Verify page contains item           ${SharedExperiment3}       xpath://*[@class='nav-link' and @href='/']

TEST CASE 7.7: Edit Experiment

    Edit Experiment         ${SharedExperiment3}   EditTestuser  EditTestInstitution  EditTestingDescription

TEST CASE 7.8: Add Experiment Metadata

    Add Experiment Metadata     TestSchema   Adding value to Param 1    Adding value to Param 2

TEST CASE 7.9: Edit Experiment Metadata

    Edit Experiment Metadata    EditParam1      EditParam2

TEST CASE 7.10: Add Dataset

    Add DataSet                 ${DatasetName}        DataDirectory       DataInstrument

TEST CASE 7.11: Verify Dataset is displayed on My Data page

    Verify page contains item   ${DatasetName}     xpath://*[@class='nav-link' and @href='/mydata/']

TEST CASE 7.12: Verify Dataset is displayed on Home page

    Verify page contains item    ${DatasetName}     xpath://*[@class='nav-link' and @href='/']

TEST CASE 7.13: Edit Dataset

    Edit DataSet            ${EditDataSetName}        EditDataDirectory       EditDataInstrument

TEST CASE 7.14: Add Dataset Metadata

    Add Dataset MetaData    DatasetSchema   Adding value to Param 1    Adding value to Param 2

TEST CASE 7.15: Edit Dataset Metadata

    Edit Dataset MetaData   Edit Adding value to Param 1        Edit Adding value to Param 2

TEST CASE 7.16: Verify user can see experiment under Shared page

    Verify page contains item       ${SharedExperiment3}       xpath://*[@class='nav-link' and @href='/shared/']

TEST CASE 7.17: Verify user can Not see experiment under Mydata page

    Open page                             xpath://*[@class='nav-link' and @href='/mydata/']
    Verify page does Not contain item     element      ${SharedExperiment3}

