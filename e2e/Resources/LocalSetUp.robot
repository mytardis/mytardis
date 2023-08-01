*** Settings ***

Library    SeleniumLibrary

*** Variables ***
${HOST}           https://demo-store.erc.monash.edu/
${BROWSER}        chrome

*** Keywords ***

Open Home page

    Open Browser    ${HOST}    browser=chrome
    Maximize Browser Window
    Capture Page Screenshot