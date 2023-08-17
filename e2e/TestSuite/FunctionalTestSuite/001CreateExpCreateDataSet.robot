*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/LocalSetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test experiement creation, adding metadata to experiment, adding datasets to experiment, adding metadata to experiment

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 1.1: Login as user

    Login       nouran      nouran

TEST CASE 1.2: Create Experiment

    Create Experiment        ${ExperimentName}       Testuser   TestInstitution   Testing description

TEST CASE 1.3: Verify Experiment is displayed on MyData page

    Verify page contains item    ${ExperimentName}     xpath://*[@class='nav-link' and @href='/mydata/']

TEST CASE 1.4: Verify Experiment is displayed on Home page

    Verify page contains item   ${ExperimentName}    xpath://*[@class='nav-link' and @href='/']

TEST CASE 1.5: Edit Experiment

    Edit Experiment         ${EditExperimentName}   EditTestuser  EditTestInstitution  EditTestingDescription

TEST CASE 1.6: Add Experiment Metadata

    Add Experiment Metadata     ${ExpSchema}   ${ExpSchemaParam1}    ${ExpSchemaParam2}
    sleep   5
TEST CASE 1.7: Edit Experiment Metadata

    Edit Experiment Metadata    EditParam1      EditParam2
    sleep   5
TEST CASE 1.8: Add Dataset

    Add DataSet                 ${DatasetName}        DataDirectory       DataInstrument
    sleep   5
TEST CASE 1.9: Verify Dataset is displayed on My Data page

    Verify page contains item   ${DatasetName}     xpath://*[@class='nav-link' and @href='/mydata/']
    sleep   5
TEST CASE 1.10: Verify Dataset is displayed on Home page

    Verify page contains item    ${DatasetName}     xpath://*[@class='nav-link' and @href='/']
    sleep   5
TEST CASE 1.11: Edit Dataset

    Edit DataSet            ${EditDataSetName}        EditDataDirectory       EditDataInstrument
    sleep   5
TEST CASE 1.12: Add Dataset Metadata

    Add Dataset MetaData    Dataset     Param 1    Param 2
    sleep   5
TEST CASE 1.13: Edit Dataset Metadata

    Edit Dataset MetaData   Edit Param 1        Edit Param 2
    sleep   5