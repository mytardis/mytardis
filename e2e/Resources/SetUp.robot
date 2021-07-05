*** Settings ***

Library    SeleniumLibrary


*** Keywords ***

Open Home page

    open browser    http://localhost:8000/      chrome
    maximize browser window

Close Browsers
    close all browsers