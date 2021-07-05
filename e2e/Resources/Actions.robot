*** Settings ***

Library    SeleniumLibrary
Documentation    This file is to test experiement creation, adding metadata to experiment, adding datasets to experiment, adding metadata to experiment

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

Create Experiment
    [Arguments]                         ${ExperimentName}      ${ExperimentAuthor}    ${Institution}    ${Description}

    wait until element is enabled       xpath://*[@class='nav-link' and @href='/mydata/']
    click element                       xpath://*[@class='nav-link' and @href='/mydata/']

    wait until element is enabled       id:create-experiment
    click element                       id:create-experiment

    Add Experiment Details              ${ExperimentName}      ${ExperimentAuthor}    ${Institution}    ${Description}
    page should contain                 ${ExperimentName}

    #Open My Data page and verify Experiment is displayed
    #click element                       xpath://*[@class='nav-link' and @href='/mydata/']
    #page should contain                 ${ExperimentName}

    #Open Home page and verify Experiment is displayed
    click element                       xpath://*[@class='nav-link' and @href='/']
    wait until element is enabled       xpath://*[contains(text(),'${ExperimentName}')]
    element should contain              xpath://*[contains(text(),'${ExperimentName}')]      ${ExperimentName}

    #Reopen Experiment
    click element                       xpath://*[contains(text(),'${ExperimentName}')]

Edit Experiment
    [Arguments]                         ${ExperimentName}      ${ExperimentAuthor}    ${Institution}    ${Description}

    wait until element is enabled       xpath://*[@class='btn btn-sm btn-outline-secondary']
    click element                       xpath://*[@class='btn btn-sm btn-outline-secondary']

    Add Experiment Details              ${ExperimentName}      ${ExperimentAuthor}    ${Institution}    ${Description}
    page should contain                 ${ExperimentName}

Add Experiment Metadata
    [Arguments]                         ${Schema}       ${Param1}       ${Param2}
    wait until element is enabled       xpath://*[@title='Metadata']
    click element                       xpath://*[@title='Metadata']

    wait until element is enabled       xpath://*[@title='Add']
    click element                       xpath://*[@title='Add']

    wait until element is enabled       id:schemaselect
    select from list by label           id:schemaselect                 ${Schema}

    wait until element is enabled       id:id_Test Parameter 1__1
    input text                          id:id_Test Parameter 1__1       ${Param1}

    wait until element is enabled       id:id_Test Parameter 2__1
    input text                          id:id_Test Parameter 2__1       ${Param2}

    wait until element is enabled       xpath://*[@class='col-md-12 text-right']//*[@class='submit-button btn btn-primary']
    click button                        xpath://*[@class='col-md-12 text-right']//*[@class='submit-button btn btn-primary']

    press keys    None      ESC

    #page should contain                 ${Param1}
    #page should contain                 ${Param2}

Add DataSet
    [Arguments]                         ${Description}   ${Directory}    ${Instrument}

    wait until element is enabled       id:add-dataset
    click element                       id:add-dataset

    Add DataSet Details                 ${Description}   ${Directory}    ${Instrument}
    page should contain                 ${Description}

    #Open My Data page and verify Experiment is displayed
   # click element                       xpath://*[@class='nav-link' and @href='/mydata/']
   # page should contain                 ${Description}

   # click element                       xpath://*[@class='nav-link' and @href='/']
   # wait until element is enabled       xpath://*[contains(text(),'${Description}')]
   # element should contain              xpath://*[contains(text(),'${Description}')]      ${Description}

    #Reopen Experiment
   # click element                       xpath://*[contains(text(),'${Description}')]

Edit DataSet
    [Arguments]                         ${Description}   ${Directory}    ${Instrument}

    wait until element is enabled       xpath://*[@class='btn btn-outline-secondary btn-sm' and @title='Edit Dataset']
    click element                       xpath://*[@class='btn btn-outline-secondary btn-sm' and @title='Edit Dataset']

    Add DataSet Details                 ${Description}   ${Directory}    ${Instrument}
    page should contain                 ${Description}

Add Dataset MetaData
    [Arguments]                         ${Schema}       ${Param1}       ${Param2}

    wait until element is enabled       xpath://*[@title='Add']
    click element                       xpath://*[@title='Add']

    wait until element is enabled       id:schemaselect
    select from list by label           id:schemaselect                 ${Schema}

    wait until element is enabled       id:id_Dataset Param 1__1
    input text                          id:id_Dataset Param 1__1        ${Param1}

    wait until element is enabled       id:id_Dataset Param 2__1
    input text                          id:id_Dataset Param 2__1        ${Param2}

    wait until element is enabled       xpath://*[@class='col-md-12 text-right']//*[@class='submit-button btn btn-primary']
    click button                        xpath://*[@class='col-md-12 text-right']//*[@class='submit-button btn btn-primary']

    press keys    None      ESC
    #page should contain                 ${Param1}
    #page should contain                 ${Param2}

Add Experiment Details
    [Arguments]                         ${ExperimentName}      ${ExperimentAuthor}    ${Institution}    ${Description}

    wait until element is enabled       id:title
    input text                          id:title                        ${ExperimentName}

    wait until element is enabled       id:authors
    input text                          id:authors                      ${ExperimentAuthor}

    wait until element is enabled       id:institution_name
    input text                          id:institution_name              ${Institution}

    wait until element is enabled       id:description
    input text                          id:description                   ${Description}

    wait until element is enabled       xpath://*[@class='offset-md-2 col-md-9 text-right']//button
    click button                        xpath://*[@class='offset-md-2 col-md-9 text-right']//button

Add DataSet Details
    [Arguments]                         ${Description}   ${Directory}    ${Instrument}

    wait until element is enabled       id:id_description
    input text                          id:id_description         ${Description}

    wait until element is enabled       id:id_directory
    input text                          id:id_directory           ${Directory}

    wait until element is enabled       xpath://*[@class='offset-md-2 col-md-9 text-right']//button
    click button                        xpath://*[@class='offset-md-2 col-md-9 text-right']//button


Verify page contains item
    [Arguments]         ${Item}


