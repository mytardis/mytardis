*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/LocalSetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test anonymous access to MyTardis

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 2.1: Access Store.monash Home page

    #Verify MyTardis Home page text
    Verify page contains text       https://sdm-magnum-k8-test.cloud.edu.au     xpath://*[@class='navbar-brand']    recent public experiments
    sleep   2
TEST CASE 2.2: Access Store.monash About page

    Verify page contains text      https://sdm-magnum-k8-test.cloud.edu.au      xpath://*[@class='nav-link' and @href='/about/']    About Store.Monash
    sleep   2
TEST CASE 2.3: Access Store.monash My Data page

    Verify page contains text      https://sdm-magnum-k8-test.cloud.edu.au      xpath://*[@class='nav-link' and @href='/mydata/']    Please Log In
    sleep   2

TEST CASE 2.4: Access Store.monash Shared page

    Verify page contains text       https://sdm-magnum-k8-test.cloud.edu.au     xpath://*[@class='nav-link' and @href='/shared/']    Please Log In
    sleep   2
TEST CASE 2.5: Access Store.monash Public Data page

    Verify page contains text       https://sdm-magnum-k8-test.cloud.edu.au     xpath://*[@class='nav-link' and @href='/public_data/']    Experiments
    sleep   2




