*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 1.1:Login as user

    Login       joe     12345

TEST CASE 1.2: Create Experiment

    Create Experiment       DemoExperiment2   Testuser   TestInstitution   Testing description

TEST CASE 1.3: Edit Experiment

    Edit Experiment         EditDemoExperiment2   EditTestuser  EditTestInstitution  EditTestingDescription

TEST CASE 1.4: Add Experiment Metadata

    Add Experiment Metadata     TestSchema   Adding value to Param 1    Adding value to Param 2


TEST CASE 1.5: Add Dataset

    Add DataSet             DemoDataset2        DataDirectory       DataInstrument

TEST CASE 1.6: Edit Dataset

    Edit DataSet            EditDemoDataset2        EditDataDirectory       EditDataInstrument

TEST CASE 1.7: Add Dataset Metadata

    Add Dataset MetaData    DatasetSchema   Adding value to Param 1    Adding value to Param 2
