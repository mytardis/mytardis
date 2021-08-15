*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot
Resource   ../../Resources/ReusablePaths.robot

Documentation    This file is to test experiement creation, adding metadata to experiment, adding datasets to experiment, adding metadata to experiment

Suite Setup         Open Home page
#Suite Teardown      close all browsers

*** Variables ***
${SharedExperimentName}     SharedExp

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

    Verify page contains item           ${SharedExperimentName}       xpath://*[@class='nav-link' and @href='/']

TEST CASE 5.7: Verify user can not edit experiment

    Verify page does Not contain item    button      Edit Experiment

TEST CASE 5.8: Verify user can not add dataset

    Verify page does Not contain item    button      Add New

TEST CASE 5.9: Verify user can not add Experiment Metadata

    #Open Experiment Metadata section
    wait until element is enabled        xpath://*[@title='Metadata']
    click element                        xpath://*[@title='Metadata']

    Verify page does Not contain item    button      Add Experiment Metadata

TEST CASE 5.10: Verify user can not change Experiment Sharing settings

    #Open Experiment Sharing section
    wait until element is enabled        xpath://*[@title='Sharing']
    click element                        xpath://*[@title='Sharing']

    Verify page does Not contain item    button      Change Public Access
    Verify page does Not contain item    button      Change User Sharing
    Verify page does Not contain item    button      Change Group Sharing
    Verify page does Not contain item    button      Create New Temporary Link

TEST CASE 5.11: Verify user can see experiment under Shared page

    Verify page contains item       ${SharedExperimentName}       xpath://*[@class='nav-link' and @href='/shared/']

TEST CASE 5.12: Verify user can Not see experiment under Mydata page

    Open page                             xpath://*[@class='nav-link' and @href='/mydata/']
    Verify page does Not contain item     element      ${SharedExperimentName}







