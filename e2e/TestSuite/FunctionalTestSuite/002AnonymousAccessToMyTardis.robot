*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/SetUp.robot
Resource   ../../Resources/Actions.robot
Resource   ../../Resources/ReusableKeywords.robot

Documentation    This file is to test anonymous access to MyTardis

Suite Setup         Open Home page
Suite Teardown      close all browsers

*** Test Cases ***

TEST CASE 2.1: Access MyTardis Home page

    #Verify MyTardis Home page text
    Verify Mytardis Home Page       xpath://*[@class='navbar-brand']    MyTardis Data Store     login      most recent public experiments

TEST CASE 2.2: Access MyTardis About page

    Verify Mytardis About Page      xpath://*[@class='nav-link' and @href='/about/']    About MyTardis

TEST CASE 2.3: Access MyTardis My Data page

    Verify Mytardis page contains text            xpath://*[@class='nav-link' and @href='/mydata/']    Please Log In

TEST CASE 2.4: Access MyTardis Shared page

    Verify Mytardis page contains text          xpath://*[@class='nav-link' and @href='/shared/']    Please Log In

TEST CASE 2.5: Access MyTardis Public Data page

    Verify Mytardis page contains text            xpath://*[@class='nav-link' and @href='/public_data/']    Experiments

TEST CASE 2.6: Access MyTardis Help page

    Verify MyTardis Help page                     xpath://*[@class='nav-link' and @href='http://mytardis.readthedocs.io/en/v4.5.0-rc2/userguide.html']