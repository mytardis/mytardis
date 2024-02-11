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
${SharedExperiment3}        SharedExp3

*** Test Cases ***

TEST CASE 7.1:Login as user

    Login                   ${User1}     ${User1PSWD}

TEST CASE 7.2: Create Experiment

    Create Experiment        ${SharedExperiment3}       Testuser   TestInstitution   Testing description

TEST CASE 7.3: Add user to Experiment Sharing as View Only

    Add new user to Sharing             ${User2}       Full Owner

TEST CASE 7.4: Verify user permissions are displayed under User Sharing

    Verify user permissions are displayed       ${User2}      Read
    Verify user permissions are displayed       ${User2}      Edit
    Verify user permissions are displayed       ${User2}      Owner

    Logout

TEST CASE 7.5:Login as user

    Login       ${User2}      ${User2PSWD}

TEST CASE 7.6: Verify user can view and open experiment under Home page

    Verify page contains item           ${SharedExperiment3}       xpath://*[@class='nav-link' and @href='/']

TEST CASE 7.7: Edit Experiment

    Edit Experiment         ${SharedExperiment3}   EditTestuser  EditTestInstitution  EditTestingDescription

TEST CASE 7.8: Add Experiment Metadata

    Add Metadata     True    ${ExpSchema}   ${SchemaParamID}    ${SchemaParamValue}

TEST CASE 7.9: Add Dataset

    Add DataSet                 ${DatasetName}        DataDirectory       DataInstrument

TEST CASE 7.10: Verify Dataset is displayed on My Data page

    Verify page contains item   ${DatasetName}     xpath://*[@class='nav-link' and @href='/mydata/']

TEST CASE 7.11: Verify Dataset is displayed on Home page

    Verify page contains item    ${DatasetName}     xpath://*[@class='nav-link' and @href='/']

TEST CASE 7.12: Edit Dataset

    Edit DataSet            ${EditDataSetName}        EditDataDirectory       EditDataInstrument

TEST CASE 7.13: Add Dataset Metadata

    Add MetaData    False   ${DatasetSchema}     ${SchemaParamID}    ${SchemaParamValue}

TEST CASE 7.14: Verify user can see experiment under Shared page

   Open page                             xpath://*[@class='nav-link' and @href='/shared/']
   Verify page does Not contain item     element      ${SharedExperiment3}

TEST CASE 7.15: Verify user can Not see experiment under Mydata page

    Open page                             xpath://*[@class='nav-link' and @href='/mydata/']
    Verify page does Not contain item     element      ${SharedExperiment3}

