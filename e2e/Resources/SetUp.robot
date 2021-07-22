*** Settings ***

Library    SeleniumLibrary

*** Variables ***

${HOST}           %{MYTARDIS_URL}
${BROWSER}        %{BROWSER}


*** Keywords ***

Open Home page

    open browser    ${HOST}      ${BROWSER}
    maximize browser window

Close Browsers
    close all browsers