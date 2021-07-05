*** Settings ***

Library    SeleniumLibrary

Resource   ../../Resources/SetUp.robot

Suite Setup     Open Home page
#Suite Teardown  close all browsers

*** Test Cases ***

TEST CASE 1.1:Create User


        python -c ../../Resources/CreateUser.py



