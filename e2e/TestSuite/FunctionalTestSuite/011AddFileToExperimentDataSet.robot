*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/LocalSetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test experiement creation, adding datasets to experiment, adding files to the dataset

Suite Setup         Open Home page
#Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 11.1:Login as user

    Login       nouran     nouran

TEST CASE 11.2: Create Experiment

    Create Experiment        ${ExperimentName}       Testuser   TestInstitution   Testing description

TEST CASE 11.3: Add Dataset

    Add DataSet                 ${DatasetName}        DataDirectory       DataInstrument

TEST CASE 11.4: Add Files to dataset

    Upload Files
