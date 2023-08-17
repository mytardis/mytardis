*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/InputData.robot
Resource   ../../Resources/LocalSetUp.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test experiement creation, adding datasets to experiment, adding files to the dataset

Suite Setup         Open Home page
#Suite Teardown      close all browsers



*** Test Cases ***

TEST CASE 12.1: Login

    Login       nouran.khattab@monash.edu     test1234

TEST CASE 12.2: Create draft Publication

    Open My Publications page
    Create Publication
    Edit Publication        False  ${PublicationTitleValue}  ${PublicationDescriptionValue}  ${SelectExperimentValue}  ${SelectDatasetValue}  ${DatasetDescriptionValue}   ${AuthorsName1Value}    ${AuthorsInstitution1Value}  ${AuthorsEmail1Value}   ${AuthorsName2Value}    ${AuthorsInstitution2Value}  ${AuthorsEmail2Value}   ${SelectAcknowledgmentValue}   ${SelectLicenseValue}   ${ReleaseDateValue}
    Save Publication as Draft

TEST CASE 12.3: Edit draft Publication

    Open draft Publication        ${PublicationTitleValue}
    Edit Publication        True  ${EditPublicationTitleValue}  ${EditPublicationDescriptionValue}  ${EditSelectExperimentValue}  ${EditSelectDatasetValue}  ${EditDatasetDescriptionValue}   ${EditAuthorsName1Value}    ${EditAuthorsInstitution1Value}  ${EditAuthorsEmail1Value}   ${EditAuthorsName2Value}    ${EditAuthorsInstitution2Value}  ${EditAuthorsEmail2Value}   ${EditSelectAcknowledgmentValue}   ${EditSelectLicenseValue}   ${EditReleaseDateValue}
    Save Publication as Draft

TEST CASE 12.4: Delete draft Publication

    Delete draft Publication    ${PublicationTitleValue}

TEST CASE 12.5: Submit Publication

   Create Publication
   Edit Publication        False  ${PublicationTitleValue}  ${PublicationDescriptionValue}  ${SelectExperimentValue}  ${SelectDatasetValue}  ${DatasetDescriptionValue}   ${AuthorsName1Value}    ${AuthorsInstitution1Value}  ${AuthorsEmail1Value}   ${AuthorsName2Value}    ${AuthorsInstitution2Value}  ${AuthorsEmail2Value}   ${SelectAcknowledgmentValue}   ${SelectLicenseValue}   ${ReleaseDateValue}
   Submit Publication







*** Keywords ***

Open My Publications page

    Wait Until Element Is Enabled     ${MyPublicationsLink}     30
    Click Element    ${MyPublicationsLink}
    Take Screenshot

Create Publication

    Wait Until Element Is Visible    ${CreatePublicationbtn}  30
    Click Button    ${CreatePublicationbtn}
    Take Screenshot

Edit Publication
    [Arguments]    ${EditMode}  ${PublicationTitleValue}  ${PublicationDescriptionValue}  ${SelectExperimentValue}  ${SelectDatasetValue}  ${DatasetDescriptionValue}   ${AuthorsName1Value}    ${AuthorsInstitution1Value}  ${AuthorsEmail1Value}   ${AuthorsName2Value}    ${AuthorsInstitution2Value}  ${AuthorsEmail2Value}   ${SelectAcknowledgmentValue}   ${SelectLicenseValue}   ${ReleaseDateValue}

    #Select Dataset
    Wait Until Element Is Enabled                               ${PublicationTitle}       30
    Input Text      ${PublicationTitle}                         ${PublicationTitleValue}        True
    Input Text      ${PublicationDescription}                   ${PublicationDescriptionValue}  True

    Select From List By Label       ${SelectExperiment}         ${SelectExperimentValue}
    Wait Until Element Is Enabled    ${SelectDataset}           30
    Input Text      ${SelectDataset}                            ${SelectDatasetValue}
    Wait Until Element Is Enabled    ${SelectDatasetOption}     30
    Select From List By Label        ${SelectDatasetOption}     ${SelectDatasetValue}
    Take Screenshot
    Sleep    3
    #Add Extra Information
    Wait Until Element Is Enabled       ${Nextbtn}  30
    Click Button        ${Nextbtn}

    Wait Until Element Is Enabled       ${DatasetDescription}   30
    Input Text         ${DatasetDescription}     ${DatasetDescriptionValue}
    Take Screenshot
    Sleep    3
    #Add Attribution
    Wait Until Element Is Enabled       ${Nextbtn}  30
    Click Button        ${Nextbtn}

    Wait Until Element Is Enabled           ${AuthorsName1}  30
    
    Run Keyword If    ${EditMode}       Click Element    xpath://*[@name="authors.0.email"]//parent::th/following-sibling::th/span[@role="button"]
    Wait Until Element Is Enabled           ${AuthorsName1}  30

    Run Keyword Unless    ${EditMode}   Input Text      ${AuthorsName1}         ${AuthorsName1Value}
    Run Keyword Unless    ${EditMode}   Input Text      ${AuthorsInstitution1}  ${AuthorsInstitution1Value}
    Run Keyword Unless    ${EditMode}   Input Text      ${AuthorsEmail1}        ${AuthorsEmail1Value}
    
    Wait Until Element Is Enabled    ${AddAuthor}       30
    Run Keyword Unless    ${EditMode}     Click Button    ${AddAuthor}

    Run Keyword Unless    ${EditMode}   Input Text      ${AuthorsName2}         ${AuthorsName2Value}
    Run Keyword Unless    ${EditMode}   Input Text      ${AuthorsInstitution2}  ${AuthorsInstitution2Value}
    Run Keyword Unless    ${EditMode}   Input Text      ${AuthorsEmail2}        ${AuthorsEmail2Value}

    Select From List By Label       ${SelectAcknowledgment}     ${SelectAcknowledgmentValue}
    Take Screenshot
    sleep  3
    #Add License and Release
    Wait Until Element Is Enabled       ${Nextbtn}  30
    Click Button        ${Nextbtn}

    Wait Until Element Is Enabled    ${SelectLicense}   30
    Select From List By Label        ${SelectLicense}   ${SelectLicenseValue}
    Input Text    ${ReleaseDate}     ${ReleaseDateValue}
    SeleniumLibrary.Press Keys    None  TAB
    Select Checkbox                  ${Consent}
    Take Screenshot
    Sleep    3

Save Publication as Draft
    Click Button                     ${SaveAndFinishLaterbtn} 
    Take Screenshot
    Sleep    3
Submit Publication
    Click Button                     ${PubSubmit}
    Take Screenshot

Open draft Publication
    [Arguments]            ${PublicationName}

    Wait Until Element Is Enabled    xpath://*[contains(text(),'${PublicationName}')]/../parent::div//*[@class="btn btn-primary btn-sm me-2 mb-1"]      30
    Click Button                     xpath://*[contains(text(),'${PublicationName}')]/../parent::div//*[@class="btn btn-primary btn-sm me-2 mb-1"]
    Take Screenshot
    Sleep    3
    
Delete draft Publication
    [Arguments]            ${PublicationName}

    Wait Until Element Is Enabled    xpath://*[contains(text(),'${PublicationName}')]/../parent::div//*[@class="btn btn-danger btn-sm me-2 mb-1 btn btn-primary"]      30
    Click Button                     xpath://*[contains(text(),'${PublicationName}')]/../parent::div//*[@class="btn btn-danger btn-sm me-2 mb-1 btn btn-primary"]

    Wait Until Element Is Enabled    xpath://button[@class="btn btn-primary" and contains(text(),'Delete')]     30
    Click Button                     xpath://button[@class="btn btn-primary" and contains(text(),'Delete')]
    Take Screenshot
    Sleep    4


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
