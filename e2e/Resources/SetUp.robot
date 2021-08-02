*** Settings ***

Library    SeleniumLibrary

*** Variables ***
${CHROMEDRIVER_PATH}        /usr/local/bin/chromedriver
${HOST}           %{MYTARDIS_URL}
#${BROWSER}        %{BROWSER}

${HOST}           http://localhost:8000/
${BROWSER}        chrome

*** Keywords ***

Open Home page
    ${chrome_options} =     Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
    Call Method    ${chrome_options}   add_argument    headless
    Call Method    ${chrome_options}   add_argument    disable-gpu
    Call Method    ${chrome_options}   add_argument    disable-dev-shm-usage
    Call Method    ${chrome_options}   add_argument    no-sandbox
    ${options}=     Call Method     ${chrome_options}    to_capabilities

    Open Browser    ${HOST}    browser=chrome    desired_capabilities=${options}


    Maximize Browser Window
    Capture Page Screenshot