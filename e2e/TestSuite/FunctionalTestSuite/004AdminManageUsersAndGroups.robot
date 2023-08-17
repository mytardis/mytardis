*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/LocalSetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test Manage users and manage groups

Suite Setup         Open Home page
#Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 4.1:Login as user

    Login       nouran.khattab@monash.edu     test1234

TEST CASE 4.2: Create new user

    Verify Create User          Jane    jane@email.com      12345

TEST CASE 4.3: Create new group

    Verify Create Group         Jane     GroupIT

TEST CASE 4.4: View Stats Page

    View Stats Page


*** Keywords ***

Verify Create User
    [Arguments]                         ${newUser}    ${newUserEmail}   ${newUserPSWD}

    wait until element is enabled       id:userMenu
    click element                       id:userMenu
    click element                       xpath://*[@href='/group/groups/']
    wait until element is enabled       xpath://*[@title='Create User']
    click button                        xpath://*[@title='Create User']

    wait until element is enabled       id:id_username
    input text                          id:id_username      ${newUser}
    input text                          id:id_email         ${newUserEmail}
    input text                          id:id_password1     ${newUserPSWD}
    input text                          id:id_password2     ${newUserPSWD}
    Take Screenshot

    click button                        id:user
    Wait Until Element Is Visible       id:success-message
    Element Text Should Be              id:success-message   Created user: ${newUser}
    Take Screenshot


Verify Create Group
    [Arguments]                         ${newUser}      ${newGroup}

    Wait Until Element Is Visible       xpath://*[@title='Create Group']
    click button                        xpath://*[@title='Create Group']

    wait until element is enabled       id:id_addgroup
    input text                          id:id_addgroup      ${newGroup}

    input text                          id:id_groupadmin    ${newUser}
    Take Screenshot
    click button                        id:group
    Take Screenshot

    wait until element is enabled       link:${newGroup}
    click element                       link:${newGroup}
    Take Screenshot