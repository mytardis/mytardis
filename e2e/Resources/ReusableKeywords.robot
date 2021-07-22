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

Verify Mytardis page contains text
     [Arguments]                        ${Page}         ${Text}
     go to                              http://localhost:8000
     wait until element is enabled      ${Page}
     click element                      ${Page}
     page should contain                ${Text}