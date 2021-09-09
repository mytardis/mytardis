*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test MAnage Users and manage groups

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 4.1:Login as user

    Login       joe     12345

TEST CASE 4.2: Create new user

    Verify Create User
    sleep   5
TEST CASE 4.3: Create new group

    Verify Create Group
    sleep   5
TEST CASE 4.4: View Stats Page

    View Stats Page
    sleep   5

