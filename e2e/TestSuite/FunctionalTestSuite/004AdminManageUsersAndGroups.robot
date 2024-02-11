*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/LocalSetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test Manage users and manage groups from Admin menu

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 4.1:Login as user

    Login       Nouran.Khattab@monash.edu      Nouran123@

TEST CASE 4.2: Create new user

    Create User          Jane    jane@email.com      12345

TEST CASE 4.3: Create another user

    Create User         John    john@email.com      12345

TEST CASE 4.4: Create new group

    Create Group         Jane     GroupIT

TEST CASE 4.5: Add user to group

    Add user to group   John    Yes


#TEST CASE 4.6: Delete user from group



#TEST CASE 4.5: View Stats Page

#    View Stats Page


*** Keywords ***

Create User
    [Arguments]                         ${newUser}    ${newUserEmail}   ${newUserPSWD}

    wait until element is enabled       id:userMenu         30
    click element                       id:userMenu
    Wait Until Element Is Enabled       xpath://*[@href='/group/groups/']   30
    click element                       xpath://*[@href='/group/groups/']
    wait until element is enabled       xpath://*[@title='Create User']
    click button                        xpath://*[@title='Create User']

    wait until element is enabled       id:id_username      30
    input text                          id:id_username      ${newUser}
    input text                          id:id_email         ${newUserEmail}
    input text                          id:id_password1     ${newUserPSWD}
    input text                          id:id_password2     ${newUserPSWD}
    Take Screenshot
    Sleep    3
    click button                        id:user
    Wait Until Element Is Visible       id:success-message      30
    Element Text Should Be              id:success-message   Created user: ${newUser}
    Take Screenshot
    Sleep    3

Create Group
    [Arguments]                         ${newUser}      ${newGroup}

    Wait Until Element Is Visible       xpath://*[@title='Create Group']
    click button                        xpath://*[@title='Create Group']

    wait until element is enabled       id:id_addgroup
    input text                          id:id_addgroup      ${newGroup}

    input text                          id:id_groupadmin    ${newUser}
    Take Screenshot
    click button                        id:group
    Take Screenshot
    Sleep    3
    wait until element is enabled       link:${newGroup}
    click element                       link:${newGroup}
    Take Screenshot
    Sleep    3

Add user to group
    [Arguments]                         ${newUser}      ${IsGroupAdmin}

    Wait Until Element Is Enabled       name:adduser    30
    Input Text                          name:adduser    ${newUser}
    SeleniumLibrary.Press Keys       None   RETURN
    Run Keyword If                      '${IsGroupAdmin}' == 'Yes'  Select Checkbox    name:admin
    Click Button                        xpath://*[@class='btn btn-primary']
    Take Screenshot


#Delete user from group
#    [Arguments]                         ${DeleteUser}

#                                        xpath://*[@class='group']//*[contains(text(),'GroupSW2')]//parent::h4
#//*[@class='group']//*[contains(text(),'GroupIT')]//parent::h4/following-sibling::div//*[contains(text(),'Jane')]
