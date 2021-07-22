*** Settings ***

Library    SeleniumLibrary

*** Variables ***

#${HOST}           %{MYTARDIS_URL}
#${BROWSER}        %{BROWSER}

${HOST}           http://localhost:8000/
${BROWSER}        chrome

*** Keywords ***

Open Home page

    open browser    ${HOST}      ${BROWSER}
    maximize browser window

Close Browsers
    close all browsers