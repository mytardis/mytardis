*** Settings ***
Library    SeleniumLibrary

*** Keywords ***

Login
    [Arguments]                      ${name}        ${password}

    wait until element is enabled    id:login-button
    click element                    id:login-button

    wait until element is enabled    id:id_username
    input text                       id:id_username     ${name}

    wait until element is enabled    id:id_password
    input text                       id:id_password     ${password}

    wait until element is enabled    id:login-button
    click button                     id:login-button

Verify page contains item
    [Arguments]         ${Item}         ${Page}
    #Open page and verify item is displayed
    click element                       ${Page}
    wait until element is enabled       link:${Item}
    click element                       link:${Item}

Verify page contains text
     [Arguments]                        ${Page}         ${Text}
     go to                              http://localhost:8000
     wait until element is enabled      ${Page}
     click element                      ${Page}
     page should contain                ${Text}

Verify page does Not contain item
     [Arguments]                        ${Page}         ${item}         ${Text}
     go to                              http://localhost:8000
     wait until element is enabled      ${Page}
     click element                      ${Page}
     Run keyword if                     '${item}'=='text'         page should not contain            ${Text}
     Run keyword if                     '${item}'=='button'       page should not contain button     ${Text}
     Run keyword if                     '${item}'=='element'      page should not contain element        ${Text}


Logout

     wait until element is enabled      xpath://*[@href='#user-menu']
     click element                      xpath://*[@href='#user-menu']
     wait until element is enabled      xpath://*[@class='dropdown-item' and @href='/logout/']
     click element                      xpath://*[@class='dropdown-item' and @href='/logout/']
