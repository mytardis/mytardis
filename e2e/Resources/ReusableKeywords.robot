*** Settings ***
Library    SeleniumLibrary

*** Keywords ***

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