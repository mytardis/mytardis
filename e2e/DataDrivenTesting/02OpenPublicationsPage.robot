*** Settings ***
Library    SeleniumLibrary
Resource   ../Resources/LocalSetUp.robot
Resource   ../Resources/ReusableKeywords.robot

Documentation    This file is open Publications page

*** Test Cases ***

Open My Publications page

*** Keywords ***

Open My Publications page

    Wait Until Element Is Enabled     ${MyPublicationsLink}     30
    Click Element    ${MyPublicationsLink}

*** Variables ***

${MyPublicationsLink}           css:a[href="/apps/publication-workflow/my-publications/"]
${CreatePublicationbtn}         css:button.pull-right

