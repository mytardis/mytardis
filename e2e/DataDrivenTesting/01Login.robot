*** Settings ***
Library    SeleniumLibrary

Resource   ../Resources/LocalSetUp.robot
Resource   ../Resources/ReusableKeywords.robot

Documentation    This file is to login to store.monash

Suite Setup         Open Home page

*** Test Cases ***

Login as user

    Login       nouran.khattab@monash.edu     test1234

