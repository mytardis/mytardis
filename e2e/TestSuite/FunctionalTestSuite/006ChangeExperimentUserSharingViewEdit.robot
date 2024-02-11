*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/LocalSetUp.robot
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

    Login                   ${User2}     ${User2PSWD}

TEST CASE 6.2: Create Experiment

    Create Experiment        ${SharedExperiment2}       Testuser   TestInstitution   Testing description

TEST CASE 6.3: Add user to Experiment Sharing as View Only

    Add new user to Sharing             ${User1}      View and Edit

TEST CASE 6.4: Verify user permissions are displayed under User Sharing

    Verify user permissions are displayed       ${User1}      Read
    Verify user permissions are displayed       ${User1}      Edit

    Logout

TEST CASE 6.5:Login as user

    Login       ${User1}      ${User1PSWD}

TEST CASE 6.6: Verify user can view and open experiment under Home page

    Verify page contains item           ${SharedExperiment2}       xpath://*[@class='nav-link' and @href='/']

TEST CASE 6.7: Edit Experiment

    Edit Experiment         ${SharedExperiment2}   EditTestuser  EditTestInstitution  EditTestingDescription

TEST CASE 6.8: Add Experiment Metadata

    Add Metadata     True    ${ExpSchema}   ${SchemaParamID}    ${SchemaParamValue}

TEST CASE 6.9: Add Dataset

    Add DataSet                 ${DatasetName}        DataDirectory       DataInstrument

TEST CASE 6.10: Verify Dataset is Not displayed on My Data page

    Verify page does Not contain item   ${DatasetName}     xpath://*[@class='nav-link' and @href='/mydata/']

TEST CASE 6.11: Verify Dataset is displayed on Home page

    Verify page contains item    ${DatasetName}     xpath://*[@class='nav-link' and @href='/']

TEST CASE 6.12: Edit Dataset

    Edit DataSet            ${EditDataSetName}        EditDataDirectory       EditDataInstrument

TEST CASE 6.13: Add Dataset Metadata

    Add MetaData    False   ${DatasetSchema}     ${SchemaParamID}    ${SchemaParamValue}

TEST CASE 6.14: Verify user can see experiment under Shared page

    Verify page contains item       ${SharedExperiment2}       xpath://*[@class='nav-link' and @href='/shared/']


TEST CASE 6.15: Verify user can Not see experiment under Mydata page

    Open page                             xpath://*[@class='nav-link' and @href='/mydata/']
    Verify page does Not contain item     element      ${SharedExperiment2}








