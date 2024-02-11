*** Settings ***

Library    SeleniumLibrary

*** Variables ***
${HOST}          https://sdm-magnum-k8-test.cloud.edu.au
${BROWSER}       chrome

*** Keywords ***

Open Home page

    Open Browser    ${HOST}    browser=chrome
    Maximize Browser Window
    Capture Page Screenshot

