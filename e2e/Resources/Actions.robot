*** Settings ***

Library    SeleniumLibrary
Resource   ../Resources/ReusableKeywords.robot

*** Keywords ***

Create Experiment
    [Arguments]                         ${ExperimentName}      ${ExperimentAuthor}    ${Institution}    ${Description}

    wait until element is enabled       xpath://*[@class='nav-link' and @href='/mydata/']
    click element                       xpath://*[@class='nav-link' and @href='/mydata/']

    wait until element is enabled       id:create-experiment
    click element                       id:create-experiment

    Add Experiment Details              ${ExperimentName}      ${ExperimentAuthor}    ${Institution}    ${Description}
    page should contain                 ${ExperimentName}

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

    wait until element is enabled       id:schemaselect            15
    select from list by label           id:schemaselect                 ${Schema}

    wait until element is enabled       id:id_Description__1        15
    input text                          id:id_Description__1            ${Param1}

    wait until element is enabled       id:id_ID__1                 15
    input text                          id:id_ID__1                     ${Param2}

    wait until element is enabled       xpath://*[@class='col-md-12']//*[@class='submit-button btn btn-primary']
    click button                        xpath://*[@class='col-md-12']//*[@class='submit-button btn btn-primary']

    seleniumLibrary.press keys    None      ESC

    #Verify Experiment Metadata are displayed under Metadata section
    wait until page contains            ${Param1}           15
    page should contain                 ${Param2}


Edit Experiment Metadata
    [Arguments]                         ${Param1}       ${Param2}
    wait until element is enabled       xpath://*[@class='edit-metadata btn btn-sm btn-outline-secondary']
    click element                       xpath://*[@class='edit-metadata btn btn-sm btn-outline-secondary']

    wait until element is enabled       id:id_Description__1        15
    input text                          id:id_Description__1            ${Param1}

    wait until element is enabled       id:id_ID__1                 15
    input text                          id:id_ID__1                     ${Param2}

    wait until element is enabled       xpath://*[@class='col-md-12']//*[@class='submit-button btn btn-primary']
    click button                        xpath://*[@class='col-md-12']//*[@class='submit-button btn btn-primary']

    seleniumLibrary.press keys    None      ESC

    #Verify Experiment Metadata are displayed under Metadata section
    wait until page contains            ${Param1}                   15
    page should contain                 ${Param2}


Add DataSet
    [Arguments]                         ${Description}   ${Directory}    ${Instrument}

    wait until element is enabled       id:add-dataset   30
    click element                       id:add-dataset

    Add DataSet Details                 ${Description}   ${Directory}    ${Instrument}
    Wait Until Page Contains            ${Description}    30

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

    #Verify Dataset Metadata are displayed on Dataset page
    wait until page contains            ${Param1}
    page should contain                 ${Param2}


Edit Dataset MetaData
    [Arguments]                         ${Param1}       ${Param2}

    wait until element is enabled       xpath://*[@class='edit-metadata btn btn-sm btn-outline-secondary']
    click element                       xpath://*[@class='edit-metadata btn btn-sm btn-outline-secondary']

    wait until element is enabled       id:id_Dataset Param 1__1
    input text                          id:id_Dataset Param 1__1        ${Param1}

    wait until element is enabled       id:id_Dataset Param 2__1
    input text                          id:id_Dataset Param 2__1        ${Param2}

    wait until element is enabled       xpath://*[@class='col-md-12 text-right']//*[@class='submit-button btn btn-primary']
    click button                        xpath://*[@class='col-md-12 text-right']//*[@class='submit-button btn btn-primary']

    press keys    None      ESC

    #Verify Dataset Metadata are displayed on Dataset page
    wait until page contains            ${Param1}
    page should contain                 ${Param2}


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

    wait until element is enabled       xpath://*[@class='btn btn-primary me-2']
    click button                        xpath://*[@class='btn btn-primary me-2']

Add DataSet Details
    [Arguments]                         ${Description}   ${Directory}    ${Instrument}

    wait until element is enabled       id:id_description
    input text                          id:id_description         ${Description}

    wait until element is enabled       id:id_directory
    input text                          id:id_directory           ${Directory}

    wait until element is enabled       xpath://*[@class='btn btn-primary me-2']
    click button                        xpath://*[@class='btn btn-primary me-2']

Verify Mytardis Home Page
    [Arguments]                         ${Page}     ${Text1}    ${Text2}    ${Text3}

    click element                       ${Page}
    wait until page contains            ${Text1}
    page should contain                 ${Text2}
    page should contain                 ${Text3}

Verify Mytardis About Page
    [Arguments]                         ${Page}     ${Heading}
      click element                     ${Page}
      page should contain               ${Heading}

      #Verify user can open Mytardis site
      page should contain               mytardis.org

      #Verify user can open Mytardis GitHub
      page should contain               GitHub

      #Verify user can see PubMed link on About page
      page should contain               [PubMed]

      #Verify user can open Mytardis contact page
      page should contain                http://www.mytardis.org/contact/

      #Verify user can open MyTardis User Guide
      #wait until element is enabled     xpath://*[@class='list-unstyled']//a[@href='http://mytardis.readthedocs.io/en/v4.5.0-rc2/userguide.html']
      #click element                     xpath://*[@class='list-unstyled']//a[@href='http://mytardis.readthedocs.io/en/v4.5.0-rc2/userguide.html']
      #switch window                     new
      #${href}                           get location
      #should be equal as strings        ${href}         https://mytardis.readthedocs.io/en/v4.5.0-rc2/userguide.html

      #Verify user can open MyTardis Documentation
      go to                             http://localhost:8000/about/
      #wait until element is enabled     xpath://*[@class='list-unstyled']//a[@href='http://mytardis.readthedocs.org/en/v4.5.0-rc2/index.html']
      #click element                     xpath://*[@class='list-unstyled']//a[@href='http://mytardis.readthedocs.org/en/v4.5.0-rc2/index.html']
      #switch window                     new
      #${href}                           get location
      #should be equal as strings        ${href}         https://mytardis.readthedocs.io/en/v4.5.0-rc2/index.html

Verify MyTardis Help page
    [Arguments]                         ${Page}
      wait until element is enabled     ${Page}
      click element                     ${Page}
      switch window                     new
      #${href}                           get location
      #should be equal as strings        ${href}         https://mytardis.readthedocs.io/en/v4.5.0-rc2/userguide.html


View Facility Page

    wait until element is enabled        xpath://*[@class='nav-link' and @href='/facility/overview/']
    click element                        xpath://*[@class='nav-link' and @href='/facility/overview/']
    page should contain                  Facility Overview


View Stats Page

    wait until element is enabled        xpath://*[@class='nav-link' and @href='/stats/']
    click element                        xpath://*[@class='nav-link' and @href='/stats/']
    page should contain                  Stats
    page should contain                  Experiments stored
    page should contain                  Datasets stored
    page should contain                  Files stored
    page should contain                  Data stored (at least)

View SFTP Instructions page
    [Arguments]                          ${ExperimentName}      ${DatasetName}
    wait until element is enabled        xpath://*[@title='Download with SFTP']
    click element                        xpath://*[@title='Download with SFTP']

    switch window                        new
    sleep    3
    page should contain                  ${ExperimentName}
    page should contain                  ${DatasetName}

    element should contain                xpath://html/body/div/div[3]/div/div/div/p[3]/a     ${ExperimentName}
    element should contain                xpath://html/body/div/div[3]/div/div/div/p[3]/a     ${DatasetName}

    element should contain                xpath://html/body/div/div[3]/div/div/div/table/tbody/tr[6]/td[2]      ${ExperimentName}
    element should contain                xpath://html/body/div/div[3]/div/div/div/table/tbody/tr[6]/td[2]      ${DatasetName}

View SFTP Keys page
     [Arguments]                          ${ExperimentName}      ${DatasetName}

    click element                         xpath://*[@href='/apps/sftp/keys/']
    page should contain                   SSH Keys
