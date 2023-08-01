*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/LocalSetUp.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test experiement creation, adding datasets to experiment, adding files to the dataset

Suite Setup         Open Home page
#Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 12.1:Login as user

    Login       nouran.khattab@monash.edu     test1234

TEST CASE 12.2: Create Publication

    Open My Publications page
    Create Publications     ${PublicationTitleValue}  ${PublicationDescriptionValue}  ${SelectExperimentValue}  ${SelectDatasetValue}  ${DatasetDescriptionValue}   ${AuthorsName1Value}    ${AuthorsInstitution1Value}  ${AuthorsEmail1Value}   ${AuthorsName2Value}    ${AuthorsInstitution2Value}  ${AuthorsEmail2Value}   ${SelectAcknowledgmentValue}   ${SelectLicenseValue}   ${ReleaseDateValue}


*** Keywords ***

Open My Publications page

    Wait Until Element Is Enabled     ${MyPublicationsLink}     30
    Click Element    ${MyPublicationsLink}
    Wait Until Element Is Enabled     ${CreatePublicationbtn}   30
    Click Button    ${CreatePublicationbtn}

Create Publications
    [Arguments]    ${PublicationTitleValue}  ${PublicationDescriptionValue}  ${SelectExperimentValue}  ${SelectDatasetValue}  ${DatasetDescriptionValue}   ${AuthorsName1Value}    ${AuthorsInstitution1Value}  ${AuthorsEmail1Value}   ${AuthorsName2Value}    ${AuthorsInstitution2Value}  ${AuthorsEmail2Value}   ${SelectAcknowledgmentValue}   ${SelectLicenseValue}   ${ReleaseDateValue}
    
    #Select Dataset
    Wait Until Element Is Enabled                               ${PublicationTitle}       30
    Input Text      ${PublicationTitle}                         ${PublicationTitleValue}
    Input Text      ${PublicationDescription}                   ${PublicationDescriptionValue}
    Select From List By Label       ${SelectExperiment}         ${SelectExperimentValue}
    Wait Until Element Is Enabled    ${SelectDataset}           30
    Input Text      ${SelectDataset}                            ${SelectDatasetValue}
    Wait Until Element Is Enabled    ${SelectDatasetOption}     30
    Select From List By Label        ${SelectDatasetOption}     ${SelectDatasetValue}

    #Add Extra Information
    Wait Until Element Is Enabled       ${Nextbtn}  30
    Click Button        ${Nextbtn}

    Wait Until Element Is Enabled       ${DatasetDescription}   30
    Input Text         ${DatasetDescription}     ${DatasetDescriptionValue}

    #Add Attribution
    Wait Until Element Is Enabled       ${Nextbtn}  30
    Click Button        ${Nextbtn}

    Wait Until Element Is Enabled           ${AuthorsName1}  30
    Input Text      ${AuthorsName1}         ${AuthorsName1Value}
    Input Text      ${AuthorsInstitution1}  ${AuthorsInstitution1Value}
    Input Text      ${AuthorsEmail1}        ${AuthorsEmail1Value}
    
    Wait Until Element Is Enabled    ${AddAuthor}       30
    Click Button    ${AddAuthor}
    Input Text      ${AuthorsName2}         ${AuthorsName2Value}
    Input Text      ${AuthorsInstitution2}  ${AuthorsInstitution2Value}
    Input Text      ${AuthorsEmail2}        ${AuthorsEmail2Value}

    Select From List By Label       ${SelectAcknowledgment}     ${SelectAcknowledgmentValue}

    #Add License and Release
    Wait Until Element Is Enabled       ${Nextbtn}  30
    Click Button        ${Nextbtn}

    Wait Until Element Is Enabled    ${SelectLicense}   30
    Select From List By Label        ${SelectLicense}   ${SelectLicenseValue}
    Input Text    ${ReleaseDate}     ${ReleaseDateValue}
    SeleniumLibrary.Press Keys    None  TAB
    Select Checkbox                  ${Consent}
    Click Button                     ${SaveAndFinishLaterbtn} 
    
    

*** Variables ***

${MyPublicationsLink}           css:a[href="/apps/publication-workflow/my-publications/"]
${CreatePublicationbtn}         css:button.pull-right
#Select Dataset
${PublicationTitle}             id:formGroupTitle
${PublicationDescription}       id:formGroupDescription
${SelectExperiment}             id:formGroupExperiment
${SelectDataset}                css:input[placeholder="Just start typing to filter datasets based on description"]
${SelectDatasetOption}          css:select[id="formGroupDatasets"]

#Add Extra Information
${DatasetDescription}           id:formGroupDatasetDescription
#Add Attribution
${SelectAcknowledgment}         id:formGroupAcknowledgement
${AuthorsName1}                 name:authors.0.name
${AuthorsInstitution1}          name:authors.0.institution
${AuthorsEmail1}                name:authors.0.email
${AuthorsName2}                 name:authors.1.name
${AuthorsInstitution2}          name:authors.1.institution
${AuthorsEmail2}                name:authors.1.email
#Add License and Release
${SelectLicense}                id:formGroupExperiment
${ReleaseDate}                  name:releaseDate
${Consent}                      name:consent


${AddAuthor}                    css:button[title="Add Author"]
${Nextbtn}                      css:button.mt-2.btn.btn-primary[type="submit"]
${Backbtn}                      css:button[class="me-2 mt-2 btn btn-primary"]
${SaveAndFinishLaterbtn}        css:button[class="mt-2 me-2 float-end btn btn-primary"][type="button"]
${PubSubmit}                    css:button[class="mt-2 me-2 float-end btn btn-primary"][type="submit"]

