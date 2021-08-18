*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test user capabilities to manage files

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 4.1: Login as user

    Login       joe     12345

TEST CASE 4.2: Open Dataset page

    Verify page contains item    ${EditDataSetName}     xpath://*[@class='nav-link' and @href='/']

TEST CASE 4.3: Open SFTP Instructions page

    View SFTP Instructions page                EditExperiment     EditDataset

TEST CASE 4.4: Open SFTP Keys page

    View SFTP Keys page                        EditExperiment     EditDataset



