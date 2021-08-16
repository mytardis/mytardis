*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot
Resource   ../../Resources/ReusablePaths.robot

Documentation    This file is to test experiement group sharing

Suite Setup         Open Home page
#Suite Teardown      close all browsers

*** Variables ***
${GroupShareExperiment}     GroupShareExperiment1

*** Test Cases ***

TEST CASE 12.1:Login as user

    Login       joe     12345

TEST CASE 12.2: Create Experiment

    Create Experiment        ${GroupShareExperiment}       Testuser   TestInstitution   Testing description

TEST CASE 12.3: Add group to Experiment Sharing as View Only

    Add new group to Sharing          TestGroup        View Only

TEST CASE 12.4: Verify user permissions are displayed under User Sharing

    Verify user permissions are displayed       TestGroup     Read

    Logout

TEST CASE 12.5:Login as user

    Login       john     12345

TEST CASE 12.6: Verify user can view and open experiment under Home page

    Verify page contains item           ${GroupShareExperiment}       xpath://*[@class='nav-link' and @href='/']

TEST CASE 12.7: Verify user can not edit experiment

    Verify page does Not contain item    button      Edit Experiment

TEST CASE 12.8: Verify user can not add dataset

    Verify page does Not contain item    button      Add New

TEST CASE 12.9: Verify user can not add Experiment Metadata

    #Open Experiment Metadata section
    wait until element is enabled        xpath://*[@title='Metadata']
    click element                        xpath://*[@title='Metadata']

    Verify page does Not contain item    button      Add Experiment Metadata

TEST CASE 12.10: Verify user can not change Experiment Sharing settings

    #Open Experiment Sharing section
    wait until element is enabled        xpath://*[@title='Sharing']
    click element                        xpath://*[@title='Sharing']

    Verify page does Not contain item    button      Change Public Access
    Verify page does Not contain item    button      Change User Sharing
    Verify page does Not contain item    button      Change Group Sharing
    Verify page does Not contain item    button      Create New Temporary Link

TEST CASE 12.11: Verify user can see experiment under Shared page

    Verify page contains item       ${GroupShareExperiment}       xpath://*[@class='nav-link' and @href='/shared/']

TEST CASE 12.12: Verify user can not see experiment under Mydata page

    Open page                             xpath://*[@class='nav-link' and @href='/mydata/']
    Verify page does Not contain item     element      ${GroupShareExperiment}







